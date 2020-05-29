import socket, threading
from node import *
import json

host = "0.0.0.0"
port = 5006
STATE_ALIVE = "ALIVE"
STATE_DEAD = "DEAD"

ACTION_JOIN = "JOIN"
ACTION_LIST = "LIST"

nodes = []

class AcceptNewNode(threading.Thread):

    def __init__(self, ip, port, clientsocket):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.csocket = clientsocket

    def run(self):

        data = self.csocket.recv(2048)
        decoded = data.decode("UTF-8")

        jsonRequest = json.load(decoded)
        action = jsonRequest["action"]
        ip = jsonRequest["ip"]
        lat = jsonRequest["lat"]
        lon = jsonRequest["lon"]

        if(action == ACTION_JOIN):
            print("Adding : " + self.ip + ":" + str(self.port))
            # adding new node
            newNode = Node(STATE_ALIVE, ip, lat, lon)
            nodes.append(newNode)
        else:
            print("Sending node list to : " + self.ip + ":" + str(self.port))
            # TODO, iterate over active nodes and send json format of nodes

        response = "Added"

        # send ack
        self.csocket.send(response.encode("utf-8"))

        self.csocket.close()


tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

tcpsock.bind((host, port))

# TODO implement hear bit monitoring & sending nodes

while True:
    tcpsock.listen(4)
    print("Listening for incoming nodes...\n")

    (clientsock, (ip, port)) = tcpsock.accept()

    # pass clientsock to the ClientThread thread object being created
    newthread = AcceptNewNode(ip, port, clientsock)
    newthread.start()