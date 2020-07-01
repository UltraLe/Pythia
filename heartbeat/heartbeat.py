import json
import socket
import threading
from time import sleep
from math import radians, cos, sin, asin, sqrt

from heartbeat.node import Node

STATE_ALIVE = "ALIVE"
STATE_DEAD = "DEAD"

REQ_JOIN = "JOIN"
REQ_LIST = "LIST"

mutexAcceptedNodes = threading.Lock()
acceptedNodes = []


class HeartBeatConnection(threading.Thread):

    def __init__(self, clientip, clientport, clientsocket):
        threading.Thread.__init__(self)
        self.ip = clientip
        self.port = clientport
        self.clientsocket = clientsocket


class SendBeatBack(HeartBeatConnection):

    def run(self):
        # if i am here, a the bootstrap is
        # asking if the node that runs this function is alive
        # no need to read the 'beat'
        response = "ALIVE"

        # HERE the self.clientsocket is the server bootstrap socket !
        self.clientsocket.send(response.encode("utf-8"))
        self.clientsocket.close()


class AcceptNewNode(HeartBeatConnection):

    def run(self):

        # receiving client request (JOIN or LIST)
        data = self.clientsocket.recv(2048)
        decoded = data.decode("UTF-8")
        jsonRequest = json.loads(decoded)

        lat = jsonRequest["lat"]
        lon = jsonRequest["lon"]

        if jsonRequest["reqtype"] == REQ_JOIN:

            ip = jsonRequest["ip"]
            beatPort = jsonRequest["beatPort"]
            print("Join Request Accepted from: " + ip + ":" + beatPort + " from " + lat + "," + lon)

            # adding the node
            newNode = Node(STATE_ALIVE, ip, lat, lon, beatPort)

            mutexAcceptedNodes.acquire()
            acceptedNodes.append(newNode)
            mutexAcceptedNodes.release()

            response = "Added"

        else:
            numFogNodes = jsonRequest["numFogNodes"]
            # print("Sending node list to : " + self.ip + ":" + str(self.port))
            response = get_node_list(lat, lon, numFogNodes)

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
    orderedNodes = acceptedNodes.copy()
    mutexAcceptedNodes.release()
    deadNodes = []
    for node in orderedNodes:
        if node.state == STATE_DEAD:
            deadNodes.append(node)
            continue
        currDistance = abs(haversine(userLon, userLat, node.lon, node.lat))
        node.distance_from_client = currDistance
        if orderedNodes.__len__() == numNodes:
            break

    for node in deadNodes:
        orderedNodes.remove(node)

    orderedNodes.sort(key=lambda x: x.distance_from_client)
    response = json.dumps(orderedNodes, default=obj_dict)
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
        # print("Node: " + self.clientip + ":" + self.clientport + " is inactive")
        mutexAcceptedNodes.acquire()
        for node in acceptedNodes:
            if node.ip == self.clientip and node.beatPort == self.clientport:
                node.state = STATE_DEAD
                mutexAcceptedNodes.release()
                break

    def run(self):
        # the server bootstrap has to connect to the client to send him th beat
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # if the server bootstrap cannot connect to the client within clienttimeout seconds,
        # raise exception...
        serversock.settimeout(self.clienttimeout)
        try:
            serversock.connect((self.clientip, int(self.clientport)))
        except (socket.timeout, socket.error) as e:
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

        # print("Response: " + beatRsponse.decode("utf-8") + " From: " + self.clientip + ":" + self.clientport)


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


# function that has to be executed by a node (server fog) after that
# he has correctly registered to the bootstrap by sending a join request
def listen_beats(host, beatPort):
    # the server fog hs to the beats on the 'beatPort' that he has specified in the JOIN REQUEST !
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, beatPort))

    while True:
        sock.listen()

        (serversock, (serverip, serverport)) = sock.accept()

        newthread = SendBeatBack(serverip, serverport, serversock)
        newthread.start()
