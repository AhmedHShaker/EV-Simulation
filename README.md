# EV-Simulation
## Overview
Welcome to the EV-Battery-Swapping project! This simulation project offers a fascinating glimpse into the world of Shared Autonomous Electric Vehicles (SAEVs) and their charging infrastructure. With this project, you can explore and analyze the operations of a fleet of autonomous electric vehicles that provide on-demand transportation services.

## About the Model
* **SAEV Fleet Model:** The SAEV fleet is modeled after the specifications of a Tesla Model 3, taking into account the average charge consumption rate and maximum battery capacity.

* **Grid Structure:** The simulation utilizes a square-shaped grid, with each Cell measuring 0.25 miles by 0.25 miles. The grid is divided into two circular regions: Downtown (center) and Suburban (outer). Each region has distinct characteristics, including vehicle travel speed and trip generation rate.

* **Charging Stations (CS):** Each CS is equipped with a pre-determined number of Chargers, each capable of serving a single SAEV at a time.

## Simulation Parameters
To allow for the simulation of various scenarios, key parameters can be modified in the ```constants.py``` file. These parameters include:

* The number of grid cells
* The fleet size (number of cars)
* The number of charging stations
* Charger count at each station
* Trip generation rates for each cell in downtown and suburban areas
* Vehicle speed
* And much more

## Simulation
The simulation is powered by the SimPy framework, a tool for creating process-based discrete-event simulations. It models the multi-agent interactions of SAEVs, Charging Stations, and user trips. Here's a simplified breakdown of how it works:

1) **Initialization:** Before the SAEV simulation begins, the charging infrastructure is dynamically generated with a pre-defined number of Chargers. The SAEVs are distributed randomly on the grid.

2) **SAEV Fleet Simulation:** The simulation consists of two main processes:
   * **SAEV Selection:** Determining the most suitable SAEVs to serve user trips.
   * **Charging Strategy:** Identifying optimal CSs for recharging, taking into account proximity and queue time.

## Getting Started
1) 📦 Clone the repository.
2) 🛠️ Install dependencies using ```pip install -r requirements.txt```.
3) ⚙️ OPTIONAL: Customize the adventure by tweaking the default values in constants.py.
4) 🏁 Run simulation.py to start the simulation and embark on your EV adventure!

Feel free to explore, modify, and contribute to this project to further enhance its capabilities. Enjoy the simulation journey! 🚀
