import math
import numpy as np
from vars import constants
from models import Car,Cell,CS
from vars import config

# Gets the Manhattan distance between 2 cells
# Result is divided by 4 because every cells is 0.25 miles
def dist(x, y):
    return (abs(x[0]-y[0]) + abs(x[1]-y[1])) / 4.0

# Gets the Euclidean distance between 2 cells
# Result is divided by 4 because every cells is 0.25 miles
def euc_dist(loc1, loc2):
    return (math.sqrt(((loc1[0]-loc2[0])**2)+((loc1[1]-loc2[1])**2))) / 4.0

# Finds the 2 possible routes between two locations
def create_route(origin, dest):
    route=[origin]
    origin2 = origin
    route2=[origin2]
    if origin[0] < dest[0] and origin[1] < dest[1]:
        first = "right"
        second = "up"
    elif origin[0] < dest[0] and origin[1] > dest[1]:
        first = "right"
        second = "down"
    elif origin[0] < dest[0] and origin[1] == dest[1]:
        first = "right"
    elif origin[0] > dest[0] and origin[1] > dest[1]:
        first = 'left'
        second = 'down'
    elif origin[0] > dest[0] and origin[1] < dest[1]:
        first = 'left'
        second = 'up'
    elif origin[0] > dest[0] and origin[1] == dest[1]:
        first = 'left'
    elif origin[0] == dest[0] and origin[1] > dest[1]:
        second = 'down'
    elif origin[0] == dest[0] and origin[1] == dest[1]:
        return []
    elif origin[0] == dest[0] and origin[1] < dest[1]:
        second = 'up'
    
    while origin[0] != dest[0]:
        
        if first == 'right':
            y = list(origin)
            y[0] += 1
            origin = tuple(y)
            route.append(origin)
        elif first == 'left':
            y = list(origin)
            y[0] -= 1
            origin = tuple(y)
            route.append(origin)
    
    while origin[1] != dest[1]:
        
        if second == 'up':
            y = list(origin)
            y[1] += 1
            origin = tuple(y)
            route.append(origin)
        elif second == 'down':
            y = list(origin)
            y[1] -= 1
            origin = tuple(y)
            route.append(origin)
    
    while origin2[1] != dest[1]:
        
        if second == 'up':
            y = list(origin2)
            y[1] += 1
            origin2 = tuple(y)
            route2.append(origin2)
        elif second == 'down':
            y = list(origin2)
            y[1] -= 1
            origin2 = tuple(y)
            route2.append(origin2) 
            
    while origin2[0] != dest[0]:
        
        if first == 'right':
            y = list(origin2)
            y[0] += 1
            origin2 = tuple(y)
            route2.append(origin2)
        elif first == 'left':
            y = list(origin2)
            y[0] -= 1
            origin2 = tuple(y)
            route2.append(origin2)       
        
    return route,route2

# Calculates the time taken for a route between 2 locations
def time_taken(origin, dest):
    if origin==dest:
        return 0
    route1,route2 = create_route(origin, dest)
    time1 = 0.0
    time2 = 0.0
    for i in range(0,len(route1)-1):
        region = get_region(route1[i])
        if region == "downtown":
            time1 += 0.25 / ((constants.DOWNTOWN_CAR_SPEED/60)/60)
        elif region == "suburban":
            time1 += 0.25 / ((constants.SUBURBAN_CAR_SPEED/60)/60)
    
    for i in range(0,len(route2)-1):
        region = get_region(route2[i])
        if region == "downtown":
            time2 += 0.25 / ((constants.DOWNTOWN_CAR_SPEED/60)/60)
        elif region == "suburban":
                time2 += 0.25 / ((constants.SUBURBAN_CAR_SPEED)/60)

    return min(time1,time2)

# Gets the region of a location
def get_region(loc):
    dist_from_center = euc_dist(loc,((constants.NUMBER_OF_CELLS-1)/2.0,(constants.NUMBER_OF_CELLS-1)/2.0))
    if dist_from_center <= constants.DOWNTOWN_AREA_RADIUS:
        return "downtown"
    else:
        return "suburban"

# Gets the CS with the best score that satisfies feasibility conditions
# This considers distance to CS and queue at CS
def get_best_score_cs(cs_copy, origin, car_charge):
    feasible_CSs = []
    for b in cs_copy:
        if b.queue >= b.num_of_chargers:
            b.score = constants.CHARGE_TIME + time_taken(origin, b.location)
        else:
            b.score = time_taken(origin, b.location)
        if car_charge >= dist(origin,b.location) * constants.CONSUMPTION_RATE:
            feasible_CSs.append(b)
    if len(feasible_CSs) == 0:
        return get_closest_station(origin,cs_copy)
    return min(feasible_CSs,key=lambda b:b.score)

# Returns the closest CS
def get_closest_station(loc, list_of_stations):
    return min(list_of_stations,key=lambda b:dist(b.location,loc))

# Get the closest available EV that meets feasibility conditions
# Feasibility conditions: Car should be available, and has enough charge to travel to user, complete the trip and travel to a CS
def get_best_feasible_ev(origin, dest, cars, nearest_station):
    min_dist = math.inf
    best = 0
    dist_to_dest = dist(origin,dest)
    for c in cars.items:
        if c.status == 'available':
            dist_to_orgin = dist(c.location,origin)
            if dist_to_orgin < min_dist:
                dist_to_station = dist(dest,nearest_station.location)
                total_dist = dist_to_orgin + dist_to_dest + dist_to_station
                consumed = constants.CONSUMPTION_RATE * total_dist
                if consumed < c.charge:
                    min_dist = dist_to_orgin
                    best = c
    if best != 0:
        return best.name
    return "none"

# A user has created the trip and the best available EV is selected to complete it
def trip(origin, dest, cars):
    i = 0
    while i < 6:
        i += 1
        name = get_best_feasible_ev(origin, dest, cars, get_closest_station(dest, config.cs_copy))
        if name != "none":
            c = yield cars.get(lambda c:c.name == name)
            c.status = "busy"
            trip_distance = dist(origin,dest)
            to_dest = dist(c.location,origin)
            distance = to_dest + trip_distance
            time_to_origin = time_taken(c.location, origin)
            time = time_to_origin + time_taken(origin, dest)
            config.waiting += time_to_origin
            
            if config.print_logs == 0 or c.name == 'Car #' + config.print_logs:
                results_file = open(constants.file_path,"a")
                results_file.write("%s started trip from %s to %s at %d\n" % (c.name,c.location, dest, config.env.now))
                results_file.close()
            yield config.env.timeout(time)
            if config.print_logs == 0 or c.name == 'Car #' + config.print_logs:
                results_file = open(constants.file_path,"a")
                results_file.write("%s completed trip (%s) at %d\n" % (c.name,dest, config.env.now))
                results_file.close()
            
            c.charge -= constants.CONSUMPTION_RATE * distance
            c.status='available'
            c.location=dest
            yield cars.put(c)
            config.completed_trips+=1
            return 1
        else:
            config.waiting += 300
            yield config.env.timeout(300)
    config.waiting -= 6*300
    config.failed_trips+=1
        
# Initialization of cells
def init_cells():
    for x in range(0,constants.NUMBER_OF_CELLS):
        for y in range(0,constants.NUMBER_OF_CELLS):
            Cell.Cell(config.env,(x,y))
            
# Initialization of cars        
def create_cars():
    for i in range(constants.NUMBER_OF_CARS):
        config.cars.items.append(Car.Car(config.env, "Car #%d"%(i+1), np.random.randint(15000,constants.MAX_CHARGE), (np.random.randint(0,constants.NUMBER_OF_CELLS-1),np.random.randint(0,constants.NUMBER_OF_CELLS-1))))

# Creates charging stations on the grid
def create_cs(number_of_cs):
    results_file = open(constants.file_path,"a")
    results_file.write("Creating charging stations...\n")
    for i in range(number_of_cs):
        cs = CS.CS(config.env, "CS #%d"%i, (np.random.randint(0,constants.NUMBER_OF_CELLS-1),np.random.randint(0,constants.NUMBER_OF_CELLS-1)), constants.NUMBER_OF_CHARGERS_PER_CS)
        results_file.write("%s --- Location: %s\n"%(cs.name, cs.location))
        config.cs_list.items.append(cs)
        config.cs_copy.append(cs)
    results_file.close()
        
# Prints the time of the simulation every 5000 seconds
def print_time():
    while True:
        results_file = open(constants.file_path,"a")
        results_file.write("Time: %d\n" % config.env.now)
        results_file.close()
        yield config.env.timeout(5000)

# Runs the SAEV simulation and displays the results
def run_saev_simulation():
    results_file = open(constants.file_path,"w")
    results_file.write("----------------------Start of SAEV Simulation----------------------\n")
    results_file.close()
    np.random.seed(constants.RANDOM_SEED)
    config.env.process(print_time())
    create_cs(constants.NUMBER_OF_CS)
    create_cars()
    init_cells()
    config.env.run(until=constants.SIM_TIME)
    
    results_file = open(constants.file_path,"a")
    results_file.write("----------------------End of SAEV Simulation----------------------\n")
    results_file.write("Total number of trips: %d\n" % config.all_trips)
    results_file.write("Number of failed trips: %d\n" % config.failed_trips)
    results_file.write("Percentage of failed trips: %f%%\n" % ((config.failed_trips/config.all_trips)*100))
    results_file.write("Number of vehicles: %d\n" % constants.NUMBER_OF_CARS)
    results_file.write("Average trips per vehicle: %f\n" % (config.completed_trips/constants.NUMBER_OF_CARS))
    results_file.write("Average customer waiting time per trip: %f seconds\n" % (config.waiting/config.completed_trips))
    results_file.write("Number of CS: %d\n" % constants.NUMBER_OF_CS)
    results_file.write("Average time spent waiting to charge per vehicle: %f seconds\n" % (config.charge_wait/constants.NUMBER_OF_CARS))
    results_file.write("Average time spent charging per charge: %f seconds\n" % (config.time_spent_charging/config.num_of_charges))
    results_file.write("Average number of charges per CS: %f\n" % (config.num_of_charges/constants.NUMBER_OF_CS))
    results_file.write("Average wait time per charge: %f seconds\n" % (config.charge_wait/config.num_of_charges))

    for c in config.cs_copy:
        utilization = ((c.used/c.num_of_chargers)/constants.SIM_TIME)*100
        results_file.write("Name: %s Location: (%d,%d) Number of stations: %d Utilization: %f%%\n" % (c.name,c.location[0],c.location[1],c.num_of_chargers,utilization))
    results_file.close()