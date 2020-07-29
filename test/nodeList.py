import threading
from time import sleep

import sys
sys.path.insert(1, '/home/ec2-user/Pythia')
from heartbeat.heartbeat import fog_nodes_list_request

host = "18.158.140.168"
# port used by bootstrap to accept new nodes
# and send the list of the registered nodes
ACCEPT_LIST_PORT = 11111


def list_requestor():
    while 1:
        print("Requesting")
        fog_nodes_list_request(host, ACCEPT_LIST_PORT, 10, "1234.21", "1232.221")
        print("Requested")
        sleep(3)

t5 = threading.Thread(target=list_requestor)
t5.start()
