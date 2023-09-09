import simpy
from . import Charger

# Charging Stations (CS) have a location and number of chargers that recharge EVs
class CS:
    def __init__(self, env, name, location, num_of_chargers):
        self.env = env
        self.name = name
        self.location = location
        self.chargers = simpy.FilterStore(env, capacity=num_of_chargers)
        self.create_chargers(num_of_chargers)
        self.num_of_chargers = num_of_chargers
        self.used = 0
        self.score = 0
        self.queue = 0
        
    def create_chargers(self, num_of_chargers):
        for _ in range(num_of_chargers):
            self.chargers.items.append(Charger.Charger(self.env))        