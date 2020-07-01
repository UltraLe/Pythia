import threading
import socket

from heartbeat.heartbeat import bootstrap_server_start, send_beats, listen_beats

host = "127.0.0.1"
# port used by bootstrap to accept new nodes
# and send the list of the registered nodes
ACCEPT_LIST_PORT = 11111


def list_requestor():
    #sleep(5)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    f = open("../heartbeat/jsonListRequestSample.json", "r")
    request = f.readlines()
    r = ""
    for x in request:
        r += x
    s.connect((host, ACCEPT_LIST_PORT))
    s.send(r.encode("utf-8"))

    response = s.recv(2048)
    decoded = response.decode("UTF-8")
    print("List received: \n"+decoded)
    s.close()


t5 = threading.Thread(target=list_requestor)
t5.start()
