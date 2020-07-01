import threading

from heartbeat.heartbeat import join_bootstrap

host = "127.0.0.1"
# port used by bootstrap to accept new nodes
# and send the list of the registered nodes
ACCEPT_LIST_PORT = 11111

def n1():
    join_bootstrap(25, "127.0.0.1", "1234.234", "3234.243", "127.0.0.1", ACCEPT_LIST_PORT,
                   1234, 10)

def n2():
    join_bootstrap(25, "127.0.0.1", "2234.234", "5234.243", "127.0.0.1", ACCEPT_LIST_PORT,
                   4321, 10)

def n3():
    join_bootstrap(25, "127.0.0.1", "1214.234", "1114.243", "127.0.0.1", ACCEPT_LIST_PORT,
                   5555, 10)


t3 = threading.Thread(target=n1)
t3.start()
t4 = threading.Thread(target=n2)
t4.start()
t5 = threading.Thread(target=n3)
t5.start()
