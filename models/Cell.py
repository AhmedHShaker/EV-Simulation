from vars import constants
from utils import common_utils as Utils
import numpy as np
from vars import config

# A cell is a single unit of the simulated area 
class Cell:
    def __init__(self, env, location):
        self.env = env
        self.location = location
        self.region = Utils.get_region(location)
        env.process(self.generate_trips())
    
    # Each cell will generate a number of trips throughout the day.
    # The number of trips depends on the location of cell (downtown, suburban...)
    # The schedule of the trips is generated randomly
    def generate_trips(self):
        schedule = []
        if self.region == "downtown":
            number_of_trips = constants.TRIPS_PER_CELL_DOWNTOWN
        else:
            number_of_trips = constants.TRIPS_PER_CELL_SUBURBAN
        for _ in range(number_of_trips):
            trip_start_time = np.random.choice(np.arange(0,constants.SIM_TIME))
            schedule.append(trip_start_time)

        i = 0
        schedule.sort()
        for t in schedule:
            if i > 0:
                yield self.env.timeout(t-schedule[i-1])
            else:
                yield self.env.timeout(t)
            config.all_trips += 1
            destination = (np.random.randint(0,constants.NUMBER_OF_CELLS-1),np.random.randint(0,constants.NUMBER_OF_CELLS-1))
            self.env.process(Utils.trip(self.location, destination, config.cars))
            i+=1