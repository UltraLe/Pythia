import json
import socket
import threading
from time import sleep

from node import Node

STATE_ALIVE = "ALIVE"
STATE_DEAD = "DEAD"

ACTION_JOIN = "JOIN"
ACTION_LIST = "LIST"

mutexOnList = threading.Lock()
acceptedNodes = []


class HeartBeatConnection(threading.Thread):

    def __init__(self, ip, port, clientsocket):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.csocket = clientsocket


class SendBeatBack(HeartBeatConnection):

    def run(self):
        # if i am here, a the bootstrap is
        # asking if the node that runs this function is alive
        # no need to read the 'beat'
        response = "ALIVE"
        self.csocket.send(response.encode("utf-8"))
        self.csocket.close()


class AcceptNewNode(HeartBeatConnection):

    def run(self):

        data = self.csocket.recv(2048)
        decoded = data.decode("UTF-8")

        jsonRequest = json.load(decoded)
        action = jsonRequest["action"]

        if (action == ACTION_JOIN):

            ip = jsonRequest["ip"]
            serverLat = jsonRequest["lat"]
            serverLon = jsonRequest["lon"]
            beatPort = jsonRequest["beatPort"]
            print("Adding : " + self.ip + ":" + str(self.port))
            # adding new node
            newNode = Node(STATE_ALIVE, ip, serverLat, serverLon, beatPort)

            mutexOnList.acquire()
            acceptedNodes.append(newNode)
            mutexOnList.release()

            response = "Added"
        else:
            print("Sending node list to : " + self.ip + ":" + str(self.port))

            userLat = jsonRequest["lat"]
            userLon = jsonRequest["lon"]
            response = get_node_list(userLat, userLon)

        self.csocket.send(response.encode("utf-8"))
        self.csocket.close()

        # after that the node has been added to the list,
        # the node itself has to launch the listenBeats function
        # in order to listen dor beats to respond to


# method that returns an array of nodes in json
def get_node_list(userLat, userLon):
    mutexOnList.acquire()
    response = json.dumps(acceptedNodes)
    mutexOnList.release()

    # TODO select here the nodes that are nearest to
    # the position given by  the user

    print("Nodes: " + response)

    return response


class SendAndReceiveBeat(threading.Thread):

    def __init__(self, ip, port, timeout):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        # it may be useful set a different timeout for different servers
        self.timeout = timeout

    def run(self):
        tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcpsock.bind((self.ip, self.port))

        beat = "Hey"
        tcpsock.send(beat.encode("utf-8"))

        # if beat is not received in X time, then mark the node as
        # INACTIVE and return
        tcpsock.listen()
        tcpsock.settimeout(self.timeout)
        print("Listening for incoming beats...\n")
        beatRsponse = ""
        try:
            (clientsock, (ip, port)) = tcpsock.accept()
            beatRsponse = clientsock.recv(2048)
            clientsock.close()
        except:
            print("Node: "+self.ip+" is inactive")
            mutexOnList.acquire()
            for node in acceptedNodes:
                if node.ip == self.ip:
                    node.state = STATE_DEAD
                    mutexOnList.release()
                    break

        print("Response: " + beatRsponse.decode("utf-8") + " From: " + self.ip)


def send_beat(timeInterval, timeout):
    while True:
        print("Waiting for beats")
        sleep(timeInterval)

        mutexOnList.acquire()
        for node in acceptedNodes:
            t = SendAndReceiveBeat(node.ip, node.beatPort, timeout)
            t.start()

        # remove after debugging
        for node in acceptedNodes:
            print("Node: "+node.ip+" Status: "+node.state)
        mutexOnList.release()


def listen_nodes(host, port):
    tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcpsock.bind((host, port))

    while True:
        tcpsock.listen()
        print("Listening for incoming nodes...\n")

        (clientsock, (ip, port)) = tcpsock.accept()

        # pass clientsock to the ClientThread thread object being created
        newthread = AcceptNewNode(ip, port, clientsock)
        newthread.start()


# function that has to be executed by a node (server fog) after that
# he has correctly registered to the bootstrap by sending a join request
def listen_beats(host, port):
    tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcpsock.bind((host, port))

    while True:
        tcpsock.listen()
        print("Listening for incoming beats...\n")

        (clientsock, (ip, port)) = tcpsock.accept()

        # pass clientsock to the ClientThread thread object being created
        newthread = SendBeatBack(ip, port, clientsock)
        newthread.start()
