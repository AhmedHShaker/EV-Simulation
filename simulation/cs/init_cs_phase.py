'''
Created on Dec 27, 2019
 
@author: Ahmed Shaker
'''

import simpy
import numpy as np
from simulation import constants
from simulation.utils import common_utils as Utils

#####################################    VARIABLES    #####################################

count = 0
numOfCharges = 0
NUMBER_OF_CS = 0
max_stations = 15

# The max number of charging stations allowed is based on the power limit of the site
if constants.CHARGE_TIME == 1860:
    max_stations = 15
elif constants.CHARGE_TIME == 2460:
    max_stations = 20
elif constants.CHARGE_TIME == 6240:
    max_stations = 50

env = simpy.Environment()
CSList = simpy.FilterStore(env)
CSCopy = []
cars = simpy.FilterStore(env, capacity=constants.NUMBER_OF_CARS)


#####################################    CLASSES    #####################################

# A station is a single charging spot in a CS
class Station:
    def __init__(self, env, status):
        self.env = env
        self.status = status
        self.born = env.now

# Charging Stations (CS) have a location and number of stations that recharge EVs
class CS:
    def __init__(self, env, name, location):
        self.env = env
        self.name = name
        self.used = 0
        self.queue = 0
        self.location = location
        self.finishTimes = []
        self.numOfStations = 0
        self.stations = simpy.FilterStore(env)
        self.stationsCopy = []
        self.createStation()
        
    def createStation(self):
        self.numOfStations += 1
        s = Station(self.env, 'empty')
        self.stations.items.append(s)
        self.stationsCopy.append(s)

# A cell is a single unit of the simulated area 
class Cell:
    def __init__(self, env, location):
        self.env = env
        self.location = location
        self.region = Utils.getRegion(location)
        env.process(self.generateTrips())
    
    # Each cell will generate a number of trips throughout the day.
    # The number of trips depends on the location of cell (downtown, urban...)
    # The schedule of the trips is random
    def generateTrips(self):
        while True:
            if self.region == "downtown":
                timeStep=int(86400/129)
            elif self.region == "urban":
                timeStep=int(86400/39)
            elif self.region == "suburban":
                timeStep=int(86400/11)
            elif self.region == "exurban":
                timeStep=86400
            env.process(trip(self.location,cars,np.random.randint(0,timeStep)))
            yield self.env.timeout(timeStep)
          
# A car transports users and travels to a CS to charge its battery  
class Car:
    def __init__(self, env, name, charge, location):  
        self.env = env
        self.status = 'available'
        self.name = name
        self.charge = charge
        self.location = location
        env.process(self.checkCharge())
         
    def checkCharge(self):
        while True:
            if self.charge < constants.MAX_CHARGE * 0.2:
                env.process(self.chargeCar())
                yield self.env.timeout(23000)
            else:
                yield self.env.timeout(300)
    
    def chargeCar(self):
        global numOfCharges
        self.status = 'busy'
        cs = getBestScoreCS(self.location, self.charge, env.now)
        time = Utils.timeTaken(self.location, cs.location, env.now)
        distance = Utils.dist(self.location,cs.location)
        yield self.env.timeout(time)
        self.charge -= constants.CONSUMPTION_RATE * distance
        self.location = cs.location
        
        myCS = 0
        x = 0
        for s in cs.stations.items:
            if s.status == 'empty':
                x = 1
                break 
        if x == 1:
            myCS = yield cs.stations.get(lambda c:c.status == 'empty')
        
        if type(myCS) != Station and cs.numOfStations < max_stations:
            myCS = getNewStation(cs)
        elif type(myCS) != Station and cs.numOfStations == max_stations:
            cs.queue += 1
            while True:
                if len(cs.stations.items) > 0:
                    for s in cs.stations.items:
                        if s.status == 'empty':
                            x = 1
                            break 
                    if x == 1:
                        myCS = yield cs.stations.get(lambda c:c.status == 'empty')
                        cs.queue -= 1
                        break
                yield self.env.timeout(60)            
            
        myCS.status = 'busy'
        chargeTime = ((constants.MAX_CHARGE-self.charge)/constants.MAX_CHARGE)*constants.CHARGE_TIME
        finishTime = env.now + chargeTime
        cs.finishTimes.append(finishTime)
        if chargeTime + env.now > constants.SIM_TIME:
            cs.used += constants.SIM_TIME - env.now
        else:
            cs.used += chargeTime
        yield env.timeout(chargeTime)
        cs.finishTimes.remove(finishTime)
        self.charge = constants.MAX_CHARGE
        myCS.status = 'empty'
        yield cs.stations.put(myCS)
        self.status = 'available'
        numOfCharges+=1


#####################################    FUNCTIONS    #####################################

# Gets the CS with the best score that satisfies feasibility conditions
# If no such CS exists, it is created
def getBestScoreCS(origin, carCharge, envNow):
    CSList.items.sort(key=lambda cs:Utils.dist(origin,cs.location))
    for cs in CSList.items:
        queueTime = 0
        if cs.queue > 0:
            cs.finishTimes.sort()
            if cs.queue < len(cs.finishTimes):
                queueTime = cs.finishTimes[cs.queue] - envNow
            else:
                queueTime = (cs.finishTimes[len(cs.finishTimes)-1]*2) - envNow
        if queueTime + Utils.timeTaken(cs.location, origin, envNow) <= constants.score_cutoff and carCharge >= Utils.dist(origin,cs.location) * constants.CONSUMPTION_RATE:
            return cs
    return createCS(origin)

# A user has created the trip and the best available EV is selected to complete it
def trip(origin, cars, startTime):
    yield env.timeout(startTime)
    cellsInRange = Utils.getCellsWithinRange(origin, Utils.getRandomTripDist())
    if len(cellsInRange) == 0:    
        cellsInRange = Utils.getCellsWithinRange(origin, 10.06)    
        dest = cellsInRange[np.random.choice(np.arange(len(cellsInRange)))]    
    else:    
        dest = cellsInRange[np.random.choice(np.arange(len(cellsInRange)))]
    
    i=0
    while i < 6:
        i+=1
        name = Utils.getBestFeasibleEV(origin, dest, cars, 0, True)
        if name != "none":
            c = yield cars.get(lambda c:c.name == name)
            c.status = "busy"
            tripDistance = Utils.dist(origin,dest)
            toDest = Utils.dist(c.location,origin)
            distance = toDest + tripDistance
            timeToOrigin = Utils.timeTaken(c.location, origin,env.now)
            time = timeToOrigin + Utils.timeTaken(origin, dest, env.now)
            yield env.timeout(time)
            c.charge -= constants.CONSUMPTION_RATE * distance
            c.status='available'
            c.location=dest
            yield cars.put(c)
            return 1
        else:
            yield env.timeout(300)

# Initialization of cells
def initCells():
    for x in range(0,200):
        for y in range(0,200):
            Cell(env,(x,y))

# Initialization of cars
def createCars():
    for i in range(constants.NUMBER_OF_CARS):
        cars.items.append(Car(env, "Car%d"%i, np.random.randint(14400,70000), (np.random.randint(0,199),np.random.randint(0,199))))

# Creates a CS at a given location
def createCS(loc):
    global count,NUMBER_OF_CS
    count+=1
    NUMBER_OF_CS+=1
    cs = CS(env, "CS%d"%count, loc)    
    CSList.items.append(cs)    
    CSCopy.append(cs)
    print("New CS Created: %s" % cs.name)
    return cs

# Creates a new station in a CS
def getNewStation(cs):
    s = Station(env, 'empty')
    cs.stations.items.append(s)
    cs.stationsCopy.append(s)
    cs.numOfStations += 1
    return s

# Counts the total number of stations in all CSs
def countStations():
    stationsCount = 0
    for cs in CSCopy:
        stationsCount += cs.numOfStations    
    return stationsCount

# Prints the time and number of CSs of the simulation every 5000 seconds
def printTime():
    while True:
        print("Time: %d. Number of CSs: %d" % (env.now,len(CSCopy)))
        yield env.timeout(5000)

# Runs the CS Generation Phase and displays the results     
def runCSGenerationPhase():
    print("----------------------Start of CS Generation Phase----------------------")
    np.random.seed(constants.RANDOM_SEED)
    env.process(printTime())
    createCars()
    initCells()
    env.run(until=constants.SIM_TIME)
    numOfStations = countStations()
    
    print("Number of vehicles: %d" % constants.NUMBER_OF_CARS)
    print("Number of CS: %d" % NUMBER_OF_CS)
    print("Total number of stations in all CS: %d" % numOfStations)
    print("Average number of stations per CS: %f" % (numOfStations/NUMBER_OF_CS))
    print("Average number of charges per CS: %f" % (numOfCharges/NUMBER_OF_CS))
    print("List of CSs created:")
    file_path = constants.text_files_path + '\\generatedCS.txt'
    CSFile = open(file_path,"w")
    for cs in CSCopy:
        print("Name: %s Location: (%d,%d) Number of stations: %d" % (cs.name,cs.location[0],cs.location[1],cs.numOfStations))
        CSFile.write("%s %d %d %d\n" % (cs.name,cs.location[0],cs.location[1],cs.numOfStations))
    CSFile.close()
    print("----------------------End of CS Generation Phase----------------------")
