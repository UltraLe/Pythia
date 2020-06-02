import threading
import socket

from heartbeat.heartbeat import listen_nodes, send_beat, listen_beats

host = "0.0.0.0"
# port used by bootstrap to accept new nodes
# and send the list of the registered nodes
ACCEPT_LIST_PORT = 1111

# port used by nodes to receive beats
BEATS_PORT = 1212

# time interval used to send beat to a server
TIME_INTERVAL_SEC = 300

# if the beat is not sent back after this time
# the node is set as inactive
TIMEOUT_SEC = TIME_INTERVAL_SEC / 2


def node_test():
    tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcpsock.bind((host, ACCEPT_LIST_PORT))
    f = open("jsonListRequestSample.json", "r")
    request = f.readlines()
    print("Sending: "+request)

    tcpsock.send(request.encode("utf-8"))

    response = tcpsock.recv(2048)
    decoded = response.decode("UTF-8")
    print("Join request response: " + decoded)

    listen_beats(host, 1234)



t1 = threading.Thread(target=listen_nodes(host, ACCEPT_LIST_PORT))
t1.start()
print("Here")
send_beat(TIME_INTERVAL_SEC, TIMEOUT_SEC)
th = threading.Thread(target=node_test())
th.start()

