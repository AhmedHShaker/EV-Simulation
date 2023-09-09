# A station is a single charging spot in a CS
class Charger:
    def __init__(self, env):
        self.env = env
        self.status = 'empty'