class Church:
    def __init__(self, name, address, link, key):
        self.name = name
        self.address = address
        self.link = link
        self.key = key
        self.dist_to_user = None
    def tostring(self):
        return self.name + " " + self.address
    def set_dist(self, distance):
        self.distance = distance
