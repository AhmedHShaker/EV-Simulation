'''
Created on Dec 27, 2019
 
@author: Ahmed Shaker
'''
import os

RANDOM_SEED = 2
NUMBER_OF_CARS = 9000                               # Number of SAEVs in the simulation
MAX_CHARGE = 72500                                  # Wh Maximum charge for a Tesla Model 3
CONSUMPTION_RATE = 230                              # Wh/mi energy consumption for Tesla Model 3 in mild weather
SWAP_TIME = 180                                     # Average seconds required to swap a battery at a BSS (180)
CHARGE_TIME = 1860                                  # Average seconds required to charge a battery at a CS (6240 for 50KW charger,  2460 for 150KW charger, 1860 for 250KW charger)
FULL_CHARGE_TIME = 31                               # Minutes required to charge a Tesla Model 3 battery. 104min for a 50KW charger, 41min for a 150 KW charger, 31min for a 250 KW charger
SIM_TIME = 86400                                    # Simulation time in seconds
score_cutoff = 900                                  # Score explained in read_me.txt
relocation_interval = 5                             # Relocation interval in minutes
intervals_in_day = (60/relocation_interval) * 24    # Number of relocation intervals in a day
text_files_path = os.path.realpath(os.path.join(os.path.dirname(__file__),'text_files'))
