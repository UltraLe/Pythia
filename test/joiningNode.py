import threading

import sys
sys.path.insert(1, '/home/ec2-user/Pythia')
from heartbeat.heartbeat import join_bootstrap, ACCEPT_LIST_PORT

boot_ip = "127.0.0.1"

def n1():
    join_bootstrap(25, "127.0.0.1", "1234.234", "3234.243", boot_ip, ACCEPT_LIST_PORT,
                   8234, 10)

def n2():
    join_bootstrap(25, "127.0.0.1", "2234.234", "5234.243", boot_ip, ACCEPT_LIST_PORT,
                   8321, 10)

def n3():
    join_bootstrap(25, "127.0.0.1", "1214.234", "1114.243", boot_ip, ACCEPT_LIST_PORT,
                   8555, 10)


t3 = threading.Thread(target=n1)
t3.start()
t4 = threading.Thread(target=n2)
t4.start()
t5 = threading.Thread(target=n3)
t5.start()
