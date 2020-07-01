class Node:

    distance_from_client = 0

    def __init__(self, state, ip, lat, lon, beatPort):
        self.lat = lat
        self.lon = lon
        self.ip = ip
        self.state = state
        self.beatPort = beatPort

    def __getstate__(self):
        return self.state

    def __setstate__(self, state):
        self.state = state


