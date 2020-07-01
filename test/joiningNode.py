import json
import threading
import socket
from time import sleep

from heartbeat.heartbeat import bootstrap_server_start, send_beats, listen_beats

host = "127.0.0.1"
# port used by bootstrap to accept new nodes
# and send the list of the registered nodes
ACCEPT_LIST_PORT = 11111


def node_test(joinRequestFile):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    f = open(joinRequestFile, "r")
    request = f.readlines()
    r = ""
    for x in request:
        r += x
    s.connect((host, ACCEPT_LIST_PORT))
    beatPort = int(json.loads(r)["beatPort"])
    s.send(r.encode("utf-8"))
    response = s.recv(2048)
    decoded = response.decode("UTF-8")
    s.close()
    listen_beats(host, beatPort)

def n1():
    node_test("joinRequestSample3.json")

def n2():
    node_test("joinRequestSample2.json")

def n3():
    node_test("../heartbeat/joinRequestSample.json")


t3 = threading.Thread(target=n1)
t3.start()
t4 = threading.Thread(target=n2)
t4.start()
t5 = threading.Thread(target=n3)
t5.start()
