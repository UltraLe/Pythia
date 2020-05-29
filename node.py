class Node:

    def __init__(self, state, ip, lat, lon):
        self.lat = lat
        self.lon = lon
        self.ip = ip
        self.state = state

    def __getstate__(self):
        return self.state

    def __setstate__(self, state):
        self.state = state


