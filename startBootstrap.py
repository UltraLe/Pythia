import threading

from heartbeat.heartbeat import bootstrap_server_start, send_beats, flood_node_list, ACCEPT_LIST_PORT, \
    CLIENT_TIMEOUT_SEC, BEAT_RATE_SEC

def listen_for_nodes():
    bootstrap_server_start("0.0.0.0", ACCEPT_LIST_PORT)


def listen_for_beats():
    send_beats(BEAT_RATE_SEC, CLIENT_TIMEOUT_SEC)

def flood_information():
    flood_node_list()


t1 = threading.Thread(target=listen_for_nodes)
t1.start()
t2 = threading.Thread(target=listen_for_beats)
t2.start()
t3 = threading.Thread(target=flood_information)
t3.start()
