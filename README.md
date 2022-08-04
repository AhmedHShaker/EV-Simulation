# EV-Battery-Swapping
## Overview
This project simulates the operations of a Shared Autonomous Electric Vehicle (SAEV) fleet that transports users on-demand in Austin, Texas. The model incorporates Battery Swapping Stations (BSS) as the charging infrastructure, and for comparison purposes, a second simulation that uses Charging Stations (CS) is created.

## Model
The SAEV fleet is modeled with the specifications of a Tesla Model 3. This includes average charge consumption rate and maximum charge of the battery.

Austin, Texas is represented by a 50-mile by 50-mile gridded metropolitan area, where each cell in the grid is 0.25-mile by 0.25-mile. The area is divided into 4 circular regions: Downtown in the center, followed by Urban, Suburban, and Exurban. Each region has a different size, vehicle travel speed and trip generation rate.

BSSs are modeled to serve a single vehicle at a time, and contain a specific number of batteries inside them. CSs contain a pre-determined number of chargers, each serving a single vehicle. The charging time for both infrastructures depends on the charger power selected (can be changed in ```constants.py```)

## Simulation
SimPy framework is used to create the process-based discrete-event simulation to model the multi-agent interactions of SAEVs, BSSs, CSs, and user trips.

Before the SAEV simulation, the BSS/CS infrastructure is generated and optimized based on location and number of batteries/chargers.
The SAEV simulation consists of multiple main processes:
1) Selecting the most suitable SAEVs to serve user trips
2) Finding optimal BSSs/CSs to swap/charge at, based on proximity and queue time
3) Relocating SAEVs to nearby areas such that vehicle supply meets trip demand

## Getting Started
1) Download the repository
2) Install dependencies using pip
```pip install -r requirements.txt```
3) OPTIONAL: Change the default values in ```constants.py```
4) Run ```sim.py``` to start the simulation
