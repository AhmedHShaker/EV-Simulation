'''
Created on Dec 27, 2019
 
@author: Ahmed Shaker
'''

import simpy
import numpy as np
from simulation import constants
from simulation.utils import common_utils as Utils

#####################################    VARIABLES    #####################################

# Counters to measure performance
NUMBER_OF_CS = 0
numOfStations = 0
allTrips = 0
trips = 0
failed = 0
failedex = 0
failedsub = 0
failedub = 0
faileddown = 0
waiting = 0
drivingTime = 0
chargeWait = 0
timeSpentCharging = 0
numOfCharges = 0
tripDist = 0
totalMiles = 0
emptyMiles = 0
emptyMilesCS = 0
totalChargeAmount = 0

# Initializing the environment
env = simpy.Environment()
CSList = simpy.FilterStore(env)
CSCopy = []
cars = simpy.FilterStore(env, capacity=constants.NUMBER_OF_CARS)
probDist = Utils.createProbDist()


#####################################    CLASSES    #####################################

# A station is a single charging spot in a CS
class Station:
    def __init__(self, env, status):
        self.env = env
        self.status = status

# Charging Stations (CS) have a location and number of stations that recharge EVs
class CS:
    def __init__(self, env, name, location, num_of_stations):
        self.env = env
        self.name = name
        self.location = location
        self.stations = simpy.FilterStore(env, capacity=num_of_stations)
        self.createStations(num_of_stations)
        self.used = 0
        self.numOfStations = num_of_stations
        self.score = 0
        self.queue = 0
        
    def createStations(self,numBatteries):
        for _ in range(numBatteries):
            self.stations.items.append(Station(self.env, 'empty'))

# A cell is a single unit of the simulated area 
class Cell:
    def __init__(self, env, location):
        self.env = env
        self.location = location
        self.region = Utils.getRegion(location)
        env.process(self.generateTrips())
    
    # Each cell will generate a number of trips throughout the day.
    # The number of trips depends on the location of cell (downtown, urban...)
    # The schedule of the trips depends on the probability distribution
    def generateTrips(self):
        global probDist, allTrips
        schedule = []
        if self.region == "downtown":
            for _ in range(129):
                schedule.append(np.random.choice(np.arange(0,86400),p=probDist))
        elif self.region == "urban":
            for _ in range(39):
                schedule.append(np.random.choice(np.arange(0,86400),p=probDist))
        elif self.region == "suburban":
            for _ in range(11):
                schedule.append(np.random.choice(np.arange(0,86400),p=probDist))
        elif self.region == "exurban":
            schedule.append(np.random.choice(np.arange(0,86400),p=probDist))

        i = 0
        schedule.sort()
        for t in schedule:
            if i > 0:
                yield self.env.timeout(t-schedule[i-1])
            else:
                yield self.env.timeout(t)
            allTrips += 1
            env.process(trip(self.location,cars))
            i+=1

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
        global chargeWait,totalMiles,emptyMiles,timeSpentCharging,emptyMilesCS,drivingTime,numOfCharges,totalChargeAmount
        self.status = 'busy'
        cs = Utils.getBestScoreCS(CSCopy, self.location, self.charge, env.now)
        time = Utils.timeTaken(self.location, cs.location,env.now)
        distance = Utils.dist(self.location,cs.location)
        totalMiles += distance
        emptyMiles += distance
        emptyMilesCS += distance
        drivingTime += time
        yield self.env.timeout(time)
        cs.queue += 1
        self.charge -= constants.CONSUMPTION_RATE * distance
        self.location = cs.location
        
        while True:
            myCS = 0
            for c in cs.stations.items:
                if c.status == 'empty':
                    myCS = yield cs.stations.get(lambda c:c.status == 'empty')
                    if type(myCS) == Station:
                        break
            if type(myCS) != Station:
                chargeWait += 60
                yield env.timeout(60)
            else:
                break
        
        myCS.status = 'busy' 
        chargeAmount = (constants.MAX_CHARGE-self.charge)
        chargeTime = (chargeAmount/constants.MAX_CHARGE)*constants.CHARGE_TIME
        if chargeTime + env.now > constants.SIM_TIME:
            cs.used += constants.SIM_TIME - env.now
        else:
            cs.used += chargeTime
        totalChargeAmount += chargeAmount
        yield env.timeout(chargeTime)
        timeSpentCharging += chargeTime
        self.charge = constants.MAX_CHARGE
        myCS.status = 'empty'
        yield cs.stations.put(myCS)
        cs.queue -= 1
        self.status = 'available'
        numOfCharges+=1


#####################################    FUNCTIONS    #####################################

# A user has created the trip and the best available EV is selected to complete it
def trip(origin, cars):
    
    cellsInRange = Utils.getCellsWithinRange(origin, Utils.getRandomTripDist())
    if len(cellsInRange) == 0:
        cellsInRange = Utils.getCellsWithinRange(origin, 10.06)
        dest = cellsInRange[np.random.choice(np.arange(len(cellsInRange)))]
    else:
        dest = cellsInRange[np.random.choice(np.arange(len(cellsInRange)))]
    
    i=0
    global failed,waiting,tripDist,totalMiles,emptyMiles,drivingTime,trips,failedex,failedsub,failedub,faileddown
    while i < 6:
        i+=1
        name = Utils.getBestFeasibleEV(origin, dest, cars, Utils.closestStation(dest,CSCopy), False)
        if name != "none":
            c = yield cars.get(lambda c:c.name == name)
            c.status = "busy"
            tripDistance = Utils.dist(origin,dest)
            toDest = Utils.dist(c.location,origin)
            distance = toDest + tripDistance
            totalMiles += distance
            tripDist += tripDistance
            emptyMiles += toDest
            timeToOrigin = Utils.timeTaken(c.location, origin,env.now)
            time = timeToOrigin + Utils.timeTaken(origin, dest,env.now)
            waiting += timeToOrigin
            drivingTime += time
            yield env.timeout(time)
            c.charge -= constants.CONSUMPTION_RATE * distance
            c.status='available'
            c.location=dest
            yield cars.put(c)
            trips+=1
            return 1
        else:
            waiting += 300
            yield env.timeout(300)
    waiting -= 6*300
    failed+=1
    region = Utils.getRegion(dest)
    if region == "exurban":
        failedex+=1
    elif region == "suburban":
        failedsub+=1
    elif region == "urban":
        failedub+=1
    elif region == "downtown":
        faileddown+=1

# Initialization of cells
def initCells():
    for x in range(0,200):
        for y in range(0,200):
            Cell(env,(x,y))

# Initialization of cars        
def createCars():
    for i in range(constants.NUMBER_OF_CARS):
        cars.items.append(Car(env, "Car%d"%i, np.random.randint(15000,70000), (np.random.randint(0,199),np.random.randint(0,199))))

# Initialization of CSs based on the CS generation phase
def createCS(points):
    global NUMBER_OF_CS, numOfStations
    for p in points:
        csItem = CS(env, p[0], (int(p[1]),int(p[2])), int(p[3]))
        CSList.items.append(csItem)
        CSCopy.append(csItem)
        numOfStations += int(p[3])
    NUMBER_OF_CS = len(points)

# Prints the time of the simulation every 5000 seconds
def printTime():
    while True:
        print("Time: %d" % env.now)
        yield env.timeout(5000)

# Runs the SAEV simulation and displays the results
def runSAEVSimulation():
    print("----------------------Start of SAEV Simulation with CSs----------------------")
    np.random.seed(constants.RANDOM_SEED)
    env.process(printTime())
    file_path = constants.text_files_path + '\\generatedCS.txt'
    points = Utils.getStationsFromFile(file_path,False)
    createCS(points)
    createCars()
    initCells()
    env.run(until=constants.SIM_TIME)
    
    print("Total number of trips: %d" % allTrips)
    print("Number of failed trips: %d" % failed)
    print("Percentage of failed trips: %f%%" % ((failed/allTrips)*100))
    print("Number of vehicles: %d" % constants.NUMBER_OF_CARS)
    print("Average trips per vehicle: %f" % (trips/constants.NUMBER_OF_CARS))
    print("Average trip distance: %f miles" % (tripDist/trips))
    print("Average miles traveled per vehicle: %f miles" % (totalMiles/constants.NUMBER_OF_CARS))
    print("Average empty miles driven per vehicle: %f miles" % (emptyMiles/constants.NUMBER_OF_CARS))
    print("Percentage of empty miles of total miles %f%%" % ((emptyMiles/totalMiles)*100))
    print("Average customer waiting time per trip: %f seconds" % (waiting/trips))
    print("Number of CS: %d" % NUMBER_OF_CS)
    print("Total number of stations in all CS: %d" % numOfStations)
    print("Average number of stations per CS: %f" % (numOfStations/NUMBER_OF_CS))
    print("Average time spent waiting to charge per vehicle: %f seconds" % (chargeWait/constants.NUMBER_OF_CARS))
    print("Average time spent charging per charge: %f seconds" % (timeSpentCharging/numOfCharges))
    print("Average number of charges per vehicle: %f" % (numOfCharges/constants.NUMBER_OF_CARS))
    print("Average number of charges per CS: %f" % (numOfCharges/NUMBER_OF_CS))
    print("Average wait time per charge: %f seconds" % (chargeWait/numOfCharges))
    print("Average empty miles driven to CS per vehicle: %f" % (emptyMilesCS/constants.NUMBER_OF_CARS))
    print("Number of failed Downtown trips: %d. Percentage of failed Downtown trips out of all failed trips: %f%%" % (faileddown, (faileddown/failed)*100))
    print("Number of failed Urban trips: %d. Percentage of failed Urban trips out of all failed trips: %f%%" % (failedub, (failedub/failed)*100))
    print("Number of failed Suburban trips: %d. Percentage of failed Suburban trips out of all failed trips: %f%%" % (failedsub, (failedsub/failed)*100))
    print("Number of failed Exurban trips: %d. Percentage of failed Exurban trips out of all failed trips: %f%%" % (failedex, (failedex/failed)*100))
    
    file_path = constants.text_files_path + '\\resultsCS.txt'
    CSFile = open(file_path,"w")
    for c in CSCopy:
        utilization = ((c.used/c.numOfStations)/constants.SIM_TIME)*100
        print("Name: %s Location: (%d,%d) Number of stations: %d Utilization: %f%%" % (c.name,c.location[0],c.location[1],c.numOfStations,utilization))
        CSFile.write("%s %d %d %d %f\n" % (c.name,c.location[0],c.location[1],c.numOfStations,utilization))
    CSFile.close()
    print("----------------------Start of SAEV Simulation with CSs----------------------")
    
    points = Utils.getStationsFromFile(file_path, True)
    Utils.showStations(points)
