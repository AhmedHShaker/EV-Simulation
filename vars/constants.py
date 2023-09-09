import os

RANDOM_SEED = 2
NUMBER_OF_CARS = 800                                # Number of SAEVs in the simulation
NUMBER_OF_CS = 8                                    # Number of CSs in the simulation
NUMBER_OF_CHARGERS_PER_CS = 5                       # Number of chargers per charging station
MAX_CHARGE = 72500                                  # Wh Maximum charge for a Tesla Model 3
CONSUMPTION_RATE = 230                              # Wh/mi energy consumption for Tesla Model 3 in mild weather
CHARGE_TIME = 1800                                  # Average seconds required to fully charge a battery at a CS
SIM_TIME = 86400                                    # Simulation time in seconds
TRIPS_PER_CELL_DOWNTOWN = 20                        # Number of trips generated per cell per day in downtown area
TRIPS_PER_CELL_SUBURBAN = 7                         # Number of trips generated per cell per day in suburban area
NUMBER_OF_CELLS = 50                                # Number of cells in the grid (50 x 50)
DOWNTOWN_AREA_RADIUS = 5                            # Radius of downtown area in miles
DOWNTOWN_CAR_SPEED = 15                             # Speed of car in downtown area (mile/hr)
SUBURBAN_CAR_SPEED = 30                             # Speed of car in suburban area (mile/hr)
file_path = os.path.realpath('results.txt')         # Path of results file