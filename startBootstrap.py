import threading

from heartbeat.heartbeat import bootstrap_server_start, send_beats

host = "0.0.0.0"
# port used by bootstrap to accept new nodes
# and send the list of the registered nodes
ACCEPT_LIST_PORT = 11111

# time interval used to send beat to a server
BEAT_RATE_SEC = 5

# if the beat is not sent back after this time
# the node is set as inactive
CLIENT_TIMEOUT_SEC = BEAT_RATE_SEC / 2


def listen_for_nodes():
    bootstrap_server_start(host, ACCEPT_LIST_PORT)


def listen_for_beats():
    send_beats(BEAT_RATE_SEC, CLIENT_TIMEOUT_SEC)


t1 = threading.Thread(target=listen_for_nodes)
t1.start()
t2 = threading.Thread(target=listen_for_beats)
t2.start()
