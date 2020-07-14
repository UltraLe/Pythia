import threading

# Aggiunto perchè a me non funziona il path -Pasquale
import sys

sys.path.insert(1, '/home/capo80/Desktop/Pythia')

from heartbeat.heartbeat import join_bootstrap


# port used by bootstrap to accept new nodes
# and send the list of the registered nodes
ACCEPT_LIST_PORT = 11111
REAL_IP = "172.74.2.203"

def n1():
    join_bootstrap(25, REAL_IP, "1234.234", "3234.243", "127.0.0.1", ACCEPT_LIST_PORT,
                   1234, 10)

def n2():
    join_bootstrap(25, REAL_IP, "2234.234", "5234.243", "127.0.0.1", ACCEPT_LIST_PORT,
                   4321, 10)

def n3():
    join_bootstrap(25, REAL_IP, "1214.234", "1114.243", "127.0.0.1", ACCEPT_LIST_PORT,
                   5555, 10)


t3 = threading.Thread(target=n1)
t3.start()
t4 = threading.Thread(target=n2)
t4.start()
t5 = threading.Thread(target=n3)
t5.start()
