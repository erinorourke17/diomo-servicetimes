class UserLoc: #location based on user input
    def __init__ (self, user_input):
        self.input = user_input
        self.geocode = None
        self.valid = True
    def set_geocode(self, geocode):
        self.geocode = geocode

    def get_geocode(self):
        return self.geocode

    def set_valid(self):
        self.valid = True