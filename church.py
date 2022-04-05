class Church:
    def __init__(self, name, address, link, key):
        self.name = name
        self.address = address
        self.link = link
        self.key = key
        self.dist_to_user = None
        self.dist_unit = None
    def tostring(self):
        return self.name + " " + self.address
    def set_dist(self, distance, dist_unit):
        self.distance = distance
        self.dist_unit = dist_unit
