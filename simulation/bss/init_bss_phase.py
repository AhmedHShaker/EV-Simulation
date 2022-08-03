'''
Created on Dec 27, 2019
 
@author: Ahmed Shaker
'''

import simpy
import numpy as np
from simulation.utils import common_utils as Utils
from simulation import constants

#####################################    VARIABLES    #####################################

# Counters to measure performance
bssCount = 0
timeSpentCharging = 0

# Initializing the environment
env = simpy.Environment()
BSSList = simpy.FilterStore(env)
BSSCopy = []
cars = simpy.FilterStore(env, capacity=constants.NUMBER_OF_CARS)


#####################################    CLASSES    #####################################

# Batteries are required to power EVs, and they recharge at BSSs
class Battery:
    def __init__(self, env, charge, owner):
        self.env = env
        self.charge = charge
        self.owner = owner
        env.process(self.chargeBattery())
    
    # As long as the battery is inside the BSS, it will charge
    def chargeBattery(self):
        while True:
            yield self.env.timeout(60)
            if self.charge < constants.MAX_CHARGE and type(self.owner) is BSS:
                self.charge += round(constants.MAX_CHARGE/constants.FULL_CHARGE_TIME)
                if self.charge > constants.MAX_CHARGE:
                    self.charge = constants.MAX_CHARGE

# Battery Swapping Stations (BSS) have a location and number of batteries, and perform battery swaps with EVs
class BSS:
    def __init__(self, env, name, location, num_of_batteries):
        self.env = env
        self.name = name
        self.location = location
        self.batteries = 0
        self.batteryList = simpy.FilterStore(env, capacity=num_of_batteries)
        self.createBatteries(1)
        self.positions = 1
        self.queue = 0
        self.score = 0
    
    # Adds a battery to the BSS
    def createBatteries(self,numBatteries):
        for _ in range(numBatteries):
            self.batteryList.items.append(Battery(self.env, constants.MAX_CHARGE, self))
            self.batteries += 1

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
            
# A car transports users and travels to a BSS to swap its battery
class Car:
    def __init__(self, env, name, charge, location):  
        self.env = env
        self.status = 'available'
        self.name = name
        self.battery = Battery(self.env, charge, self)
        self.charge = self.battery.charge
        self.location = location
        env.process(self.checkCharge())
          
    def checkCharge(self):
        while True:
            if self.charge < constants.MAX_CHARGE * 0.2:
                env.process(self.chargeCar())
                yield env.timeout(23000)
            else:
                yield env.timeout(300)
    
    def chargeCar(self):
        global timeSpentCharging
        self.status = 'busy'
        bss = Utils.getBestScoreBSS(BSSCopy, self.location, self.charge, env.now, True)
        if bss == 0:
            bss = createBSS(self.location)
            print("New BSS Created: %s" % bss.name)

        time = Utils.timeTaken(self.location, bss.location, env.now)
        distance = Utils.dist(self.location,bss.location)
        yield self.env.timeout(time)
        bss.queue += 1
        self.charge -= constants.CONSUMPTION_RATE * distance
        self.location = bss.location
        
        while True:
            if bss.positions > 0:
                myBss = yield BSSList.get(lambda b:b==bss)
                if type(myBss) == BSS:
                    bss = myBss
                    bss.positions = 0
                    break
            yield self.env.timeout(60)
        
        bestBattery = Utils.getBestBattery(bss,True)
        newBattery = 0
        if bestBattery != 0:
            newBattery = yield bss.batteryList.get(lambda b:b == bestBattery)
        if type(newBattery) != Battery:
            newBattery = getNewBattery(bss)
            
        self.battery.charge = self.charge
        self.battery.owner = bss
        yield bss.batteryList.put(self.battery)
        self.battery = newBattery
        self.battery.owner = self
        self.charge = self.battery.charge
        yield self.env.timeout(constants.SWAP_TIME)
        yield BSSList.put(bss)
        bss.queue -= 1
        bss.positions = 1
        self.status = 'available'
        timeSpentCharging += constants.SWAP_TIME


#####################################    FUNCTIONS    #####################################

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
            timeToOrigin = Utils.timeTaken(c.location, origin, env.now)
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

# Creates a BSS at a given location
def createBSS(loc):
    global bssCount
    bssCount+=1
    bss = BSS(env, "BSS%d"%bssCount, loc, 10000)
    BSSList.items.append(bss)
    BSSCopy.append(bss)
    return bss

# Initialization of cars
def createCars():
    for i in range(constants.NUMBER_OF_CARS):
        cars.items.append(Car(env, "Car%d"%i, np.random.randint(14400,70000), (np.random.randint(0,199),np.random.randint(0,199))))

# Creates a new battery in a BSS
def getNewBattery(bss):
    b = Battery(env, constants.MAX_CHARGE, bss)
    bss.batteryList.items.append(b)
    bss.batteries += 1
    return b

# Counts the total number of batteries in all BSSs
def countBatteries():
    batteriesCount = 0
    for bss in BSSCopy:
        batteriesCount += bss.batteries
    return batteriesCount

# Prints the time and number of BSSs of the simulation every 5000 seconds
def printTime():
    while True:
        print("Time: %d. Number of BSSs: %d" % (env.now,len(BSSCopy)))
        yield env.timeout(5000)

# Runs the BSS Generation Phase and displays the results
def runBSSGenerationPhase():
    print("----------------------Start of BSS Generation Phase----------------------")
    np.random.seed(constants.RANDOM_SEED)
    env.process(printTime())
    createCars()
    initCells()
    env.run(until=constants.SIM_TIME)
    numOfBatteries = countBatteries()
    NUMBER_OF_BSS = len(BSSCopy)
    print("Number of vehicles: %d" % constants.NUMBER_OF_CARS)
    print("Number of BSS: %d" % NUMBER_OF_BSS)
    print("Total number of batteries in all BSS: %d" % numOfBatteries)
    print("Average number of batteries per BSS: %f" % (numOfBatteries/NUMBER_OF_BSS))
    print("Average number of charges per BSS: %f" % ((timeSpentCharging/constants.SWAP_TIME)/NUMBER_OF_BSS))
    print("List of BSSs created:")
    
    file_path = constants.text_files_path + '\\generatedBSS.txt'
    BSSFile = open(file_path,"w")
    for b in BSSCopy:
        print("Name: %s Location: (%d,%d) Number of batteries: %d" % (b.name,b.location[0],b.location[1],b.batteries))
        BSSFile.write("%s %d %d %d\n" % (b.name,b.location[0],b.location[1],b.batteries))
    BSSFile.close()
    print("----------------------End of BSS Generation Phase----------------------")

