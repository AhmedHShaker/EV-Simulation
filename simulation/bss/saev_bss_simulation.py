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
NUMBER_OF_BSS = 0
numOfBatteries = 0
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
tripDist = 0
totalMiles = 0
emptyMiles = 0
emptyMilesBSS = 0
totalChargeAmount = 0
relocationMiles = 0

# Initializing the environment
env = simpy.Environment()
BSSList = simpy.FilterStore(env)
copyOfBSS=[]
cars = simpy.FilterStore(env, capacity=constants.NUMBER_OF_CARS)
probDist = []
listOfCells = []
listOfBlocks = []


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
        global totalChargeAmount
        while True:
            yield self.env.timeout(60)
            if self.charge < constants.MAX_CHARGE and type(self.owner) is BSS:
                self.charge += round(constants.MAX_CHARGE/constants.FULL_CHARGE_TIME)
                totalChargeAmount += round(constants.MAX_CHARGE/constants.FULL_CHARGE_TIME)
                if self.charge > constants.MAX_CHARGE:
                    totalChargeAmount = totalChargeAmount - (self.charge-constants.MAX_CHARGE)
                    self.charge = constants.MAX_CHARGE

# Battery Swapping Stations (BSS) have a location and number of batteries, and perform battery swaps with EVs
class BSS:
    def __init__(self, env, name, location, num_of_batteries):
        self.env = env
        self.name = name
        self.location = location
        self.batteryList = simpy.FilterStore(env)
        self.createBatteries(num_of_batteries)
        self.positions = 1
        self.used = 0
        self.queue = 0
        self.score = 0
    
    # Creates an initial number of batteries at the start of the simulation
    def createBatteries(self,numBatteries):
        for _ in range(numBatteries):
            self.batteryList.items.append(Battery(self.env, constants.MAX_CHARGE, self))

# A block is a collection of cells located close to a BSS location   
class Block:
    def __init__(self, name, location):
        global listOfBlocks
        self.name = name
        self.location = location
        self.demand = 0
        self.neighbors = []
        self.cells = []
        self.imbalance = 0
        self.availableCars = []
        listOfBlocks.append(self)

# A cell is a single unit of the simulated area
class Cell:
    def __init__(self, env, location):
        global probDist,allTrips,listOfCells
        self.env = env
        self.location = location
        self.region = Utils.getRegion(location)
        self.currentTrips = 0
        listOfCells.append(self)
        env.process(self.generateTrips())
    
    # Each cell will generate a number of trips throughout the day.
    # The number of trips depends on the location of cell (downtown, urban...).
    # The schedule of the trips depends on the probability distribution
    def generateTrips(self):
        global probDist,allTrips
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
            self.currentTrips += 1
            env.process(trip(self.location,cars))
            i+=1
          
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
                yield self.env.timeout(23000)
            else:
                yield self.env.timeout(300)
    
    def chargeCar(self):
        global chargeWait,totalMiles,emptyMiles,timeSpentCharging,emptyMilesBSS,drivingTime
        self.status = 'busy'
        bss = Utils.getBestScoreBSS(copyOfBSS,self.location,self.charge,env.now,False)
        time = Utils.timeTaken(self.location, bss.location,env.now)
        distance = Utils.dist(self.location,bss.location)
        totalMiles += distance
        emptyMiles += distance
        emptyMilesBSS += distance
        drivingTime += time
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
            chargeWait += 60
            yield self.env.timeout(60)
        
        while True:
            bestBattery = Utils.getBestBattery(bss,False)
            if bestBattery != 0:
                newBattery = yield bss.batteryList.get(lambda b:b == bestBattery)
                if type(newBattery) == Battery:
                    break
            chargeWait += 60
            yield self.env.timeout(60)
            
        self.battery.charge = self.charge
        self.battery.owner = bss
        yield bss.batteryList.put(self.battery)
        self.battery = newBattery
        self.battery.owner = self
        self.charge = self.battery.charge
        if constants.SWAP_TIME + env.now > constants.SIM_TIME:
            bss.used += constants.SIM_TIME - env.now
        else:
            bss.used += constants.SWAP_TIME
        yield self.env.timeout(constants.SWAP_TIME)
        yield BSSList.put(bss)
        bss.queue -=1
        bss.positions = 1
        self.status = 'available'
        timeSpentCharging += constants.SWAP_TIME


#####################################    FUNCTIONS    #####################################

# Creates blocks at the start of the simulation
def createBlocks():
    global listOfCells,listOfBlocks
    i = 1
    for bss in copyOfBSS:
        Block(i, bss.location)
        i += 1
    
    for c in listOfCells:
        block = min(listOfBlocks,key=lambda block:Utils.dist(block.location,c.location))
        c.block = block
    
    listOfCells,listOfBlocks = Utils.setNeighbors(listOfCells,listOfBlocks)

# Performs the process of EV relocation to reduce the imbalance between supply and demand in blocks
def relocation():
    global listOfCells,listOfBlocks
    listOfCells, listOfBlocks = Utils.setupBlocks(listOfCells)
    
    while True:
        listOfBlocks = Utils.setNewImbalances(listOfBlocks,listOfCells,cars)
        for c in cars.items:
            if c.status == 'available':
                b = Utils.getCell(listOfCells,c.location[0],c.location[1]).block
                relocated = False
                if b.carBalance > 0:
                    b.neighbors.sort(key=lambda x:Utils.dist(c.location,x.location))
                    for n in b.neighbors:
                        if n.carBalance < 0:
                            n.carBalance += 1
                            env.process(relocateCar(c, n.location))
                            relocated = True
                            break
                if b.carBalance < 0 or not relocated:
                    env.process(relocateCar(c, b.location))
        
        yield env.timeout(constants.relocation_interval*60)

# Relocates a car to its new destination
def relocateCar(c, dest):
    global relocationMiles
    if c.location == dest:
        return 1
    
    schedule, route = Utils.timeSchedule(c.location, dest, env.now)
    i = 0
    for r in route:
        if c.status == 'available':
            yield env.timeout(round(schedule[i]))
            c.location = r
            if i > 0:
                travelDist = Utils.dist(r,route[i-1])
                relocationMiles += travelDist
                c.charge -= constants.CONSUMPTION_RATE * travelDist
            i+=1

# A user has created the trip and the best available EV is selected to complete it (if feasibility conditions are met).
def trip(origin, cars):
    
    cellsInRange = Utils.getCellsWithinRange(origin, Utils.getRandomTripDist())
    if len(cellsInRange) == 0:
        cellsInRange = Utils.getCellsWithinRange(origin, 10.06)
        dest = cellsInRange[np.random.choice(np.arange(len(cellsInRange)))]
    else:
        dest = cellsInRange[np.random.choice(np.arange(len(cellsInRange)))]
    
    i=0
    nearestBSS = Utils.closestStation(dest,copyOfBSS)
    global failed,waiting,tripDist,totalMiles,emptyMiles,drivingTime,trips,failedex,failedsub,failedub,faileddown
    while i < 6:
        i+=1
        name = Utils.getBestFeasibleEV(origin, dest, cars, nearestBSS, False)
        if name != "none":
            c = yield cars.get(lambda c:c.name == name)
            Utils.getCell(listOfCells,origin[0], origin[1]).currentTrips -= 1
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
    failed+=1
    waiting -= 6*300
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

# Initialization of BSSs based on the BSS generation phase
def createBSS(points):
    global NUMBER_OF_BSS, numOfBatteries
    for p in points:
        bssItem = BSS(env, p[0], (int(p[1]),int(p[2])), int(p[3]))
        BSSList.items.append(bssItem)
        copyOfBSS.append(bssItem)
        numOfBatteries += int(p[3])
    NUMBER_OF_BSS = len(points)

# Prints the time of the simulation every 5000 seconds
def printTime():
    while True:
        print("Time: %d" % env.now)
        yield env.timeout(5000)

# Runs the SAEV simulation and displays the results
def runSAEVSimulation(enableRelocation,generateNewBlocks):
    print("----------------------Start of SAEV Simulation with BSSs----------------------")
    global probDist
    np.random.seed(constants.RANDOM_SEED)
    probDist = Utils.createProbDist()
    env.process(printTime())
    file_path = constants.text_files_path + '\\generatedBSS.txt'    
    points = Utils.getStationsFromFile(file_path, False)
    createBSS(points)
    createCars()
    initCells()
    if generateNewBlocks:
        createBlocks()
    if enableRelocation:
        env.process(relocation())
    
    env.run(until=constants.SIM_TIME)
    
    print("Total number of trips: %d" % allTrips)
    print("Number of failed trips: %d" % failed)
    print("Percentage of failed trips: %f%%" % ((failed/allTrips)*100))
    print("Number of vehicles: %d" % constants.NUMBER_OF_CARS)
    print("Average trips per vehicle: %f" % (trips/constants.NUMBER_OF_CARS))
    print("Average Trip Distance: %f miles" % (tripDist/trips))
    print("Average miles traveled per vehicle: %f miles" % (totalMiles/constants.NUMBER_OF_CARS))
    print("Average empty miles driven per vehicle: %f miles" % (emptyMiles/constants.NUMBER_OF_CARS))
    print("Percentage of empty miles out of total miles %f%%" % ((emptyMiles/totalMiles)*100))
    print("Average waiting time per trip: %f seconds" % (waiting/trips))
    print("Number of BSS: %d" % NUMBER_OF_BSS)
    print("Total number of batteries in all BSS: %d" % numOfBatteries)
    print("Average number of batteries per BSS: %f" % (numOfBatteries/NUMBER_OF_BSS))
    print("Average time spent waiting to charge per vehicle: %f seconds" % (chargeWait/constants.NUMBER_OF_CARS))
    print("Average time spent charging per vehicle: %f seconds" % (timeSpentCharging/constants.NUMBER_OF_CARS))
    print("Average number of charges per vehicle: %f" % ((timeSpentCharging/constants.SWAP_TIME)/constants.NUMBER_OF_CARS))
    print("Average number of charges per BSS: %f" % ((timeSpentCharging/constants.SWAP_TIME)/NUMBER_OF_BSS))
    print("Average wait time per charge: %f seconds" % (chargeWait/(timeSpentCharging/constants.SWAP_TIME)))
    print("Average empty miles driven to BSS per vehicle: %f" % (emptyMilesBSS/constants.NUMBER_OF_CARS))
    print("Number of failed Downtown trips: %d. Percentage of failed Downtown trips out of all failed trips: %f%%" % (faileddown, (faileddown/failed)*100))
    print("Number of failed Urban trips: %d. Percentage of failed Urban trips out of all failed trips: %f%%" % (failedub, (failedub/failed)*100))
    print("Number of failed Suburban trips: %d. Percentage of failed Suburban trips out of all failed trips: %f%%" % (failedsub, (failedsub/failed)*100))
    print("Number of failed Exurban trips: %d. Percentage of failed Exurban trips out of all failed trips: %f%%" % (failedex, (failedex/failed)*100))
    
    file_path = constants.text_files_path + '\\resultsBSS.txt' 
    BSSFile = open(file_path,"w")
    for b in copyOfBSS:
        utilization = (b.used/constants.SIM_TIME)*100
        print("Name: %s Location: (%d,%d) Number of batteries: %d Utilization: %f%%" % (b.name,b.location[0],b.location[1],len(b.batteryList.items),utilization))
        BSSFile.write("%s %d %d %d %f\n" % (b.name,b.location[0],b.location[1],len(b.batteryList.items),utilization))
    BSSFile.close()
    print("----------------------End of SAEV Simulation with BSSs----------------------")
    points = Utils.getStationsFromFile(file_path, True)
    Utils.showStations(points)
