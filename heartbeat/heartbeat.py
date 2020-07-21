import json
import socket
import threading
from time import sleep
from math import radians, cos, sin, asin, sqrt

from heartbeat.bootstrapRequest import BootstrapRequest
from heartbeat.node import Node

STATE_ALIVE = "ALIVE"
STATE_DEAD = "DEAD"
REQ_JOIN = "JOIN"
REQ_LIST = "LIST"
FLOOD_INFO = "FLOODING"
RESPONSE_ADDED = "ADDED"
MAX_IGNORED_BEATS = 2

# key = ip:port, value = num of beat ignored
inactive_nodes = {}

FLOOD_INTERVAL = 5
BOOTSTRAP_DOMAIN_NAME = "www.whatacoolbootstrapip.it"
ACCEPT_LIST_PORT = 11111

mutexAcceptedNodes = threading.Lock()
acceptedNodes = []

floodedNodes = []
mutexFloodedNodes = threading.Lock()

"""
        SERVER SIDE
"""


class HeartBeatConnection(threading.Thread):

    def __init__(self, clientip, clientport, clientsocket):
        threading.Thread.__init__(self)
        self.ip = clientip
        self.port = clientport
        self.clientsocket = clientsocket


class AcceptNewNode(HeartBeatConnection):

    def run(self):

        # receiving client request (JOIN or LIST)
        data = self.clientsocket.recv(2048)
        decoded = data.decode("UTF")
        jsonRequest = json.loads(decoded)

        if jsonRequest["reqtype"] != FLOOD_INFO:
            lat = jsonRequest["lat"]
            lon = jsonRequest["lon"]

        if jsonRequest["reqtype"] == REQ_JOIN:

            ip = jsonRequest["ip"]
            beatPort = jsonRequest["beatPort"]
            print("Join Request from: " + ip + ":" + str(beatPort) + " from " + lat + "," + lon)

            # adding the node
            newNode = Node(STATE_ALIVE, ip, lat, lon, beatPort)

            # but only if it is not been altrady added
            replica = False
            mutexAcceptedNodes.acquire()
            for node in acceptedNodes:
                if node.ip == newNode.ip and node.beatPort == newNode.beatPort:
                    replica = True
                    node.state = STATE_ALIVE
                    break

            if not replica:
                acceptedNodes.append(newNode)

            mutexAcceptedNodes.release()

            response = RESPONSE_ADDED

        elif jsonRequest["reqtype"] == REQ_LIST:
            numFogNodes = jsonRequest["numFogNodes"]
            print("Sending node list to : " + self.ip + ":" + str(self.port))
            response = get_node_list(lat, lon, numFogNodes)

        else:
            # jsonRequest["reqtype"] == FLOOD_INFO
            nodes = jsonRequest['nodes']
            mutexFloodedNodes.acquire()

            for node in nodes:
                nd = json.loads(node)
                newNode = Node(nd['state'], nd['ip'], nd['lat'], nd['lon'], nd['beatPort'])

                AddNode = True
                for receivedNode in floodedNodes:
                    # add node only if the node was not received earlier
                    if newNode.ip == receivedNode.ip and receivedNode.beatPort == newNode.beatPort:
                        receivedNode.state = newNode.state
                        AddNode = False
                        break

                if(AddNode):
                    floodedNodes.append(newNode)
            mutexFloodedNodes.release()

            # not needed a response for that
            self.clientsocket.close()
            return

        self.clientsocket.send(response.encode("utf-8"))
        self.clientsocket.close()
        # after that the node has been added to the list,
        # the node itself has to launch the listenBeats function
        # in order to listen dor beats to respond to


# formula used to calculate the distance in km between 2 points
# in the globe, given their latitude and longitude
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers.
    return c * r


# method that returns an array of nodes in json
def get_node_list(userLat, userLon, numNodes):
    # evaluating the distance between the client lat lon
    # and the server registered
    mutexAcceptedNodes.acquire()
    mutexFloodedNodes.acquire()
    orderedNodes = acceptedNodes.copy()
    floodedOrderedNodes = floodedNodes.copy()
    mutexAcceptedNodes.release()
    mutexFloodedNodes.release()
    activeNodes = []
    for node in orderedNodes:
        if node.state == STATE_ALIVE:
            currDistance = abs(haversine(userLon, userLat, node.lon, node.lat))
            node.distance_from_client = currDistance
            activeNodes.append(node)
            continue
        if orderedNodes.__len__() == numNodes:
            break

    for node in floodedOrderedNodes:
        if node.state == STATE_ALIVE:
            currDistance = abs(haversine(userLon, userLat, node.lon, node.lat))
            node.distance_from_client = currDistance
            activeNodes.append(node)
            continue
        if orderedNodes.__len__() == numNodes:
            break

    activeNodes.sort(key=lambda x: x.distance_from_client)
    response = json.dumps(activeNodes, default=obj_dict)
    return response


# used to retrieve the json of the node list
def obj_dict(obj):
    return obj.__dict__


class SendAndReceiveBeat(threading.Thread):

    def __init__(self, clientip, clientport, clienttimeout):
        threading.Thread.__init__(self)
        self.clientip = clientip
        self.clientport = clientport
        # it may be useful set a different timeout for different servers
        self.clienttimeout = clienttimeout

    def mark_node_inactive(self):
        print("Node: " + self.clientip + ":" + str(self.clientport) + " is inactive")
        mutexAcceptedNodes.acquire()
        for node in acceptedNodes:
            if node.ip == self.clientip and node.beatPort == self.clientport:
                node.state = STATE_DEAD
                mutexAcceptedNodes.release()

                if node.ip + str(node.beatPort) not in inactive_nodes.keys():
                    inactive_nodes[node.ip+str(node.beatPort)] = 1
                else:
                    if inactive_nodes[node.ip + str(node.beatPort)] > MAX_IGNORED_BEATS:
                        # remove node from acceptedNodes
                        mutexAcceptedNodes.acquire()
                        acceptedNodes.remove(node)
                        mutexAcceptedNodes.release()
                    else:
                        inactive_nodes[node.ip + str(node.beatPort)] += 1

                break

    def run(self):
        # the server bootstrap has to connect to the client to send him th beat
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # if the server bootstrap cannot connect to the client within clienttimeout seconds,
        # raise exception...
        serversock.settimeout(self.clienttimeout)
        try:
            serversock.connect((self.clientip, int(self.clientport)))
        except:
            # the server cannot connect to the client, the node is incative
            self.mark_node_inactive()
            serversock.close()
            return

        # resetting timer
        serversock.settimeout(None)
        beat = "Hey"
        serversock.settimeout(self.clienttimeout)
        try:
            serversock.send(beat.encode("utf-8"))
            beatRsponse = serversock.recv(2048)
            serversock.close()

        except socket.timeout:
            self.mark_node_inactive()
            serversock.close()
            return

        # print("Response: " + beatRsponse.decode("utf-8") + " From: " + self.clientip + ":" + str(self.clientport))


def send_beats(bootstrapTimeInterval, clientTimeout):
    while True:
        sleep(bootstrapTimeInterval)

        mutexAcceptedNodes.acquire()
        for node in acceptedNodes:
            t = SendAndReceiveBeat(node.ip, node.beatPort, clientTimeout)
            t.start()
        mutexAcceptedNodes.release()


def bootstrap_server_start(host, port):
    serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversock.bind((host, port))

    while True:
        serversock.listen()

        (clientsock, (clientip, clientport)) = serversock.accept()

        # pass clientsock to the ClientThread thread object being created
        newthread = AcceptNewNode(clientip, clientport, clientsock)
        newthread.start()


"""
    CLIENT SIDE
"""


class SendBeatBack(HeartBeatConnection):

    def run(self):
        # if i am here, a the bootstrap is
        # asking if the node that runs this function is alive
        # no need to read the 'beat'
        response = "ALIVE"

        # HERE the self.clientsocket is the server bootstrap socket !
        self.clientsocket.send(response.encode("utf-8"))
        self.clientsocket.close()


# function that has to be executed by a node (server fog) after that
# he has correctly registered to the bootstrap by sending a join request
def listen_beats(retryAfterSeconds, ip, lat, lon, bootstrapip, bootsrapport, beatPort, serverBootstrapTimeoutSec):
    # the server fog hs to the beats on the 'beatPort' that he has specified in the JOIN REQUEST !
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ip, beatPort))

    # if the client that has already registered on the bootstrap
    # does not hear beats coming form the bootstrap within
    # serverBootstrapTimeoutSec seconds, it assume that the bootstrap has
    # crashed and tries to join again.
    while True:
        sock.listen()
        sock.settimeout(serverBootstrapTimeoutSec)
        try:
            (serversock, (serverip, serverport)) = sock.accept()
            newthread = SendBeatBack(serverip, serverport, serversock)
            newthread.start()
            # if i am here the timer has to be restarted
            sock.settimeout(None)
        except socket.timeout:
            sock.close()
            # here i have to register again to the bootstrap
            # print("Cant hear beats from bootstrap from beatPort: " + str(beatPort) + ". Rejoining..")
            join_bootstrap(retryAfterSeconds, ip, lat, lon, bootstrapip,
                           bootsrapport, beatPort, serverBootstrapTimeoutSec)


# function executed to the clients that wants to register to the bootstrap
def join_bootstrap(retryAfterSeconds, ip, lat, lon, bootstrapip, bootsrapport, beatPort, serverBootstrapTimeoutSec):
    # if the client cannot connect to the server bootstrap,
    # raise exception, an try it again
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((bootstrapip, bootsrapport))
            # now the client is connected to the server, sending the join request
            joinRequest = BootstrapRequest(REQ_JOIN, ip, lat, lon, None, beatPort)
            jsonJoinRequest = json.dumps(joinRequest.__dict__)
            encoded = jsonJoinRequest.encode("utf-8")
            sock.send(encoded)
            response = sock.recv(2048)
            decoded = response.decode("UTF-8")
            if decoded != RESPONSE_ADDED:
                raise socket.error
            break
        except socket.error:
            # retry after retryAfterSeconds
            print("Bootstrap server seems to be down for " + str(beatPort) + ", trying again soon...")
            sleep(retryAfterSeconds)
    print("BeatPort: " + str(beatPort) + " connected to bootstrap")
    # now that the node has been accepted from the bootstrap,
    # he can listen for server beats
    listen_beats(retryAfterSeconds, ip, lat, lon, bootstrapip, bootsrapport, beatPort, serverBootstrapTimeoutSec)


# function used to request the lists of node (a total of numFogNodes nodes) registered to the
# bootstrap, ordered in increasing distance from the client that has done the request
def fog_nodes_list_request(bootstrapip, bootstrapport, numFogNodes, clientlat, clientlon):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listRequest = BootstrapRequest(REQ_LIST, bootstrapip, clientlat, clientlon, numFogNodes, None)
    jsonListRequest = json.dumps(listRequest.__dict__)

    s.connect((bootstrapip, bootstrapport))
    s.send(jsonListRequest.encode("utf-8"))

    response = s.recv(2048)
    decoded = response.decode("UTF-8")
    print("List received: \n" + decoded)
    s.close()


"""
    MULTIPLE BOOTSTRAP HANDLING
"""


def flood_node_list():
    import subprocess

    while True:
        # a = subprocess.check_output("dig +short "+BOOTSTRAP_DOMAIN_NAME, shell=True)
        # b = a.splitlines()
        # bootstrapIpList = b[:-1]
        #
        bootstrapIpList = {"10.42.0.2", "10.42.0.1"}
        # test raspberry and pc

        # myip = subprocess.check_output("dig +short myip.opendns.com @resolver1.opendns.com", shell=True)
        myip = "10.42.0.1"

        for bootStrapIP in bootstrapIpList:
            if bootStrapIP == myip:
                continue
            # send list to other bootstraps
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                floodRequest = {}
                floodRequest['reqtype'] = FLOOD_INFO
                mutexAcceptedNodes.acquire()
                nodes = acceptedNodes.copy()
                mutexAcceptedNodes.release()
                n = []
                for node in nodes:
                    n.append(json.dumps(node.__dict__))

                floodRequest['nodes'] = n

                jsonRequest = json.dumps(floodRequest)
                # print("Flooding theese informations: ", jsonRequest)
                s.connect((bootStrapIP, ACCEPT_LIST_PORT))
                s.send(jsonRequest.encode("utf-8"))
            except:
                continue

            s.close()

        sleep(FLOOD_INTERVAL)
