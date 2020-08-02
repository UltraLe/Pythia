import threading
from time import sleep

import sys
sys.path.insert(1, '/home/ec2-user/Pythia')
from heartbeat.heartbeat import fog_nodes_list_request, BOOTSTRAP_DOMAIN_NAME, ACCEPT_LIST_PORT


def list_requestor():
    while 1:
        print("Requesting")
        fog_nodes_list_request(BOOTSTRAP_DOMAIN_NAME, ACCEPT_LIST_PORT, 10, "1234.21", "1232.221")
        print("Requested")
        sleep(3)

t5 = threading.Thread(target=list_requestor)
t5.start()
