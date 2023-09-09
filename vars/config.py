import simpy
from vars import constants

# Initialize the shared counters to measure performance
all_trips = 0
completed_trips = 0
failed_trips = 0
waiting = 0
charge_wait = 0
time_spent_charging = 0
num_of_charges = 0

# Print logs shared variable
print_logs = 0

# Initialize the environment
env = simpy.Environment()
cs_list = simpy.FilterStore(env)
cars = simpy.FilterStore(env, capacity=constants.NUMBER_OF_CARS)
cs_copy = []