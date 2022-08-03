'''
Created on Dec 27, 2019
 
@author: Ahmed Shaker
'''

import math
import numpy as np
from simulation import constants
import matplotlib.pyplot as plt
import random
import pickle

# Gets the manhattan distance between 2 cells
def dist(x, y):
    return (abs(x[0]-y[0]) + abs(x[1]-y[1])) / 4.0

# Gets the euclidean distance between 2 cells
def eucDist(loc1, loc2):
    return (math.sqrt(((loc1[0]-loc2[0])**2)+((loc1[1]-loc2[1])**2))) / 4.0

# Generates a random trip distance
def getRandomTripDist():
    np.random.seed(constants.RANDOM_SEED)
    return np.random.normal(9.82,3,1)[0]

# Finds all cells within a certain range 
def getCellsWithinRange(origin, maxRange):
    cellsInRange = []
    maxRange = round(maxRange)
    for x in range(200):
        for y in range(200):
            if round(dist(origin, (x,y))) == maxRange:
                cellsInRange.append((x,y))
    return cellsInRange

# Returns if the curent time is within peak hours of the day
def peakHour(envNow):
    now = envNow % 86400
    if (now >= 25200 and now < 28800) or (now >= 59400 and now < 64800):
        return True
    return False

# Finds the 2 possible routes between two locations
def createRoute(origin, dest):
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
def timeTaken(origin, dest, envNow):
    if origin==dest:
        return 0
    route1,route2 = createRoute(origin, dest)
    time1 = 0.0
    time2 = 0.0
    for i in range(0,len(route1)-1):
        region = getRegion(route1[i])
        if region == "downtown":
            time1 += 0.25 / ((15/60)/60)
        elif region == "urban":
            time1 += 0.25 / ((24/60)/60)
        elif region == "suburban":
            if peakHour(envNow):
                time1 += 0.25 / ((30/60)/60)
            else:
                time1 += 0.25 / ((33/60)/60)
        elif region == "exurban":
            if peakHour(envNow):
                time1 += 0.25 / ((33/60)/60)
            else:
                time1 += 0.25 / ((36/60)/60)
    
    for i in range(0,len(route2)-1):
        region = getRegion(route2[i])
        if region == "downtown":
            time2 += 0.25 / ((15/60)/60)
        elif region == "urban":
            time2 += 0.25 / ((24/60)/60)
        elif region == "suburban":
            if peakHour(envNow):
                time2 += 0.25 / ((30/60)/60)
            else:
                time2 += 0.25 / ((33/60)/60)
        elif region == "exurban":
            if peakHour(envNow):
                time2 += 0.25 / ((33/60)/60)
            else:
                time2 += 0.25 / ((36/60)/60)

    return min(time1,time2)

# Gets the region of a location
def getRegion(loc):
    distFromCenter = eucDist(loc,(99.5,99.5))
    
    if distFromCenter > 15:
        return "exurban"
    elif distFromCenter > 7.5 and distFromCenter <= 15:
        return "suburban"
    elif distFromCenter > 2.5 and distFromCenter <= 7.5:
        return "urban"
    elif distFromCenter <= 2.5:
        return "downtown"

# Gets the best battery inside a BSS
def getBestBattery(bss, bssPhase):
    while True:
        highestCharge = 0        
        for b in bss.batteryList.items:
            if b.charge > highestCharge:
                bestBattery = b
                highestCharge = b.charge
                if highestCharge == constants.MAX_CHARGE:
                    return bestBattery
        if not bssPhase and highestCharge  >= constants.MAX_CHARGE * 0.8:
            return bestBattery
        else:
            return 0

# Gets the battery with the best score that satisfies feasibility conditions
def getBestScoreBSS(copyOfBSS, origin, carCharge, envNow, generationPhase):
    feasibleBSSs = []
    for b in copyOfBSS:
        b.score = (b.queue*constants.SWAP_TIME) + timeTaken(origin, b.location, envNow)
        if carCharge >= dist(origin,b.location) * constants.CONSUMPTION_RATE:
            if (generationPhase and b.score <= constants.score_cutoff) or (not generationPhase):
                feasibleBSSs.append(b)
    if len(feasibleBSSs) == 0:
        if generationPhase:
            return 0
        else:
            return closestStation(origin,copyOfBSS)
    return min(feasibleBSSs,key=lambda b:b.score)

# Gets the CS with the best score that satisfies feasibility conditions
def getBestScoreCS(CSCopy, origin, carCharge, envNow):
    feasibleCSs = []
    for b in CSCopy:
        if b.queue >= b.numOfStations:
            b.score = constants.CHARGE_TIME + timeTaken(origin, b.location,envNow)
        else:
            b.score = timeTaken(origin, b.location,envNow)
        if carCharge >= dist(origin,b.location) * constants.CONSUMPTION_RATE:
            feasibleCSs.append(b)
    if len(feasibleCSs) == 0:
        return closestStation(origin,CSCopy)
    return min(feasibleCSs,key=lambda b:b.score)

# Returns the closest BSS or CS
def closestStation(loc, listOfElements):
    return min(listOfElements,key=lambda b:dist(b.location,loc))

# Models the probability distribution of trips so that more trips are created in rush hours
def createProbDist():
    prob = []
    for t in range(86400):
        if (t >= 25200 and t < 28800) or (t >= 59400 and t < 64800):
            prob.append(1.5/90900)
        else:
            prob.append(1/90900)
    return prob

# Get the closest available EV that meets feasibility conditions
def getBestFeasibleEV(origin, dest, cars, nearestStation, generationPhase):
    minDist=math.inf
    best = 0
    distToDest = dist(origin,dest)
    for c in cars.items:
        if c.status == 'available':
            distToOrg = dist(c.location,origin)
            if distToOrg < minDist:
                totalDist = distToOrg + distToDest
                if not generationPhase:
                    totalDist += dist(dest,nearestStation.location)
                consumed = constants.CONSUMPTION_RATE * totalDist
                if consumed < c.charge:
                    minDist = distToOrg
                    best = c
    if best != 0:
        return best.name
    return "none"

# Returns the schedule and route that the EV will follow for relocation
def timeSchedule(origin,dest,envNow):
    route1,route2 = createRoute(origin, dest)
    time1 = 0.0
    time2 = 0.0
    timeSchedule1 = [0]
    timeSchedule2 = [0]
    for i in range(0,len(route1)-1):
        region = getRegion(route1[i])
        if region == "downtown":
            t = 0.25 / ((15/60)/60)
            timeSchedule1.append(t)
            time1 += t
        elif region == "urban":
            t = 0.25 / ((24/60)/60)
            timeSchedule1.append(t)
            time1 += t
        elif region == "suburban":
            if peakHour(envNow):
                t = 0.25 / ((30/60)/60)
                timeSchedule1.append(t)
                time1 += t
            else:
                t = 0.25 / ((33/60)/60)
                timeSchedule1.append(t)
                time1 += t
        elif region == "exurban":
            if peakHour(envNow):
                t = 0.25 / ((33/60)/60)
                timeSchedule1.append(t)
                time1 += t
            else:
                t = 0.25 / ((36/60)/60)
                timeSchedule1.append(t)
                time1 += t
    
    for i in range(0,len(route2)-1):
        region = getRegion(route2[i])
        if region == "downtown":
            t = 0.25 / ((15/60)/60)
            timeSchedule2.append(t)
            time2 += t
        elif region == "urban":
            t = 0.25 / ((24/60)/60)
            timeSchedule2.append(t)
            time2 += t
        elif region == "suburban":
            if peakHour(envNow):
                t = 0.25 / ((30/60)/60)
                timeSchedule2.append(t)
                time2 += t
            else:
                t = 0.25 / ((33/60)/60)
                timeSchedule2.append(t)
                time2 += t
        elif region == "exurban":
            if peakHour(envNow):
                t =  0.25 / ((33/60)/60)
                timeSchedule2.append(t)
                time2 += t
            else:
                t = 0.25 / ((36/60)/60)
                timeSchedule2.append(t)
                time2 += t

    if time1 < time2:
        return timeSchedule1,route1
    else:
        return timeSchedule2,route2

# Gets the generated BSSs or CSs from a file
def getStationsFromFile(file, includeUtilization):
    with open(file,'r') as reader:
        points = []
        for line in reader.readlines():
            values = line.split(' ')
            points.append([values[0],int(values[1]),int(values[2]), int(values[3]),0 if not includeUtilization else values[4]])
        return points

# Plots the location of BSSs or CSs and assigns them a color based on utilization
def showStations(points):
    for p in points:
        if float(p[4]) > 40:
            plt.plot(int(p[1]), int(p[2]), marker='o', color='red')
        elif float(p[4]) > 30 and float(p[4]) <= 40:
            plt.plot(int(p[1]), int(p[2]), marker='o', color='purple')
        elif float(p[4]) > 20 and float(p[4]) <= 30:
            plt.plot(int(p[1]), int(p[2]), marker='o', color='dodgerblue')
        else:
            plt.plot(int(p[1]), int(p[2]), marker='o', color='orange')
    plt.show()
    
# Calculates and sets the supply/demand imbalances in each block for EV relocation
def setNewImbalances(listOfBlocks,listOfCells,cars):
    for b in listOfBlocks:
        carCount,carList = getBlockAvailableCars(cars,listOfCells,b)
        b.imbalance =  getBlockDemand(b) - carCount
        b.availableCars = carList
    random.shuffle(listOfBlocks)
    for b in listOfBlocks:
        carsRequired = []
        carsRequired.append(b.imbalance)
        for n in b.neighbors:
            carsRequired.append(n.imbalance)
        
        surplus = 0
        deficit = 0
        carCountRelativeToRequired = {}
        for i in range(len(carsRequired)):
            carCountRelativeToRequired[i] = carsRequired[i]
            #carsRequired +ve, requires cars. carsRequired -ve, has surplus cars
            if carsRequired[i] > 0:
                deficit += abs(carsRequired[i])
            else:
                surplus += abs(carsRequired[i])
        
        for i in range(len(carsRequired)):
            if deficit > 0 and surplus > 0:
                if carsRequired[i] > 0:
                    #if surplus > deficit:
                    carCountRelativeToRequired[i] = carsRequired[i] - round((carsRequired[i] / deficit) * (surplus))
                elif carsRequired[i] < 0:
                    carCountRelativeToRequired[i] = 0
        
        totalCars = 0
        for i in range(len(carCountRelativeToRequired)):
            totalCars += carCountRelativeToRequired[i]
                
        b.newImbalance = carCountRelativeToRequired[0]
        b.carBalance = b.newImbalance - b.imbalance
        i = 1
        for n in b.neighbors:
            miscalculatedCount = 0
            if totalCars > deficit - surplus:
                miscalculatedCount = -1
                totalCars -= 1
            elif totalCars < deficit - surplus:
                miscalculatedCount = 1
                totalCars += 1
            n.newImbalance = carCountRelativeToRequired[i] + miscalculatedCount
            #if -ve, I need cars, if +ve I give cars
            n.carBalance = n.newImbalance - n.imbalance
            i += 1
    return listOfBlocks
            
# Gets the available cars inside a given block
def getBlockAvailableCars(cars,listOfCells,block):
    availableCars = 0
    carList = []
    for c in cars.items:
        if c.status == 'available' and getCell(listOfCells,c.location[0],c.location[1]).block == block:
            carList.append(c)
            availableCars += 1
            
    return availableCars, carList

# Returns a cell by location
def getCell(listOfCells,loc1,loc2):
    return listOfCells[(loc1*200) + loc2]

# Gets the current and estimateed future demand of a block within a single relocation interval
def getBlockDemand(block):
    currentDemand = 0
    futureDemand = 0
    
    for c in block.cells:
        currentDemand += c.currentTrips
        # Estimated future demand
        if c.region == "downtown":
            futureDemand += 129/constants.intervals_in_day
        elif c.region == "urban":
            futureDemand += 39/constants.intervals_in_day
        elif c.region == "suburban":
            futureDemand += 11/constants.intervals_in_day
        elif c.region == "exurban":
            futureDemand += 1/constants.intervals_in_day
            
    return round(currentDemand + futureDemand)

# Finds and sets the neighbors of each block, and saves the blocks in a file
def setNeighbors(listOfCells,listOfBlocks):
    for c in listOfCells:
        currentBlock = c.block
        if c.location[0] > 0 and c.location[0] < 199 and c.location[1] > 0 and c.location[1] < 199:
            rightCellBlock = getCell(listOfCells,c.location[0]+1, c.location[1]).block
            leftCellBlock = getCell(listOfCells,c.location[0]-1, c.location[1]).block
            northCellBlock = getCell(listOfCells,c.location[0], c.location[1]+1).block
            southCellBlock = getCell(listOfCells,c.location[0], c.location[1]-1).block
            if rightCellBlock != currentBlock:
                currentBlock.neighbors.append(rightCellBlock)
            if leftCellBlock != currentBlock:
                currentBlock.neighbors.append(leftCellBlock)
            if northCellBlock != currentBlock:
                currentBlock.neighbors.append(northCellBlock)
            if southCellBlock != currentBlock:
                currentBlock.neighbors.append(southCellBlock)
                 
        elif c.location[0] == 0 and c.location[1] == 0:
            rightCellBlock = getCell(listOfCells,c.location[0]+1, c.location[1]).block
            northCellBlock = getCell(listOfCells,c.location[0], c.location[1]+1).block
            if rightCellBlock != currentBlock:
                currentBlock.neighbors.append(rightCellBlock)
            if northCellBlock != currentBlock:
                currentBlock.neighbors.append(northCellBlock)
                 
        elif c.location[0] == 199 and c.location[1] == 199:
            leftCellBlock = getCell(listOfCells,c.location[0]-1, c.location[1]).block
            southCellBlock = getCell(listOfCells,c.location[0], c.location[1]-1).block
            if leftCellBlock != currentBlock:
                currentBlock.neighbors.append(leftCellBlock)
            if southCellBlock != currentBlock:
                currentBlock.neighbors.append(southCellBlock)
                
        elif c.location[0] == 0 and c.location[1] == 199:
            rightCellBlock = getCell(listOfCells,c.location[0]+1, c.location[1]).block
            southCellBlock = getCell(listOfCells,c.location[0], c.location[1]-1).block
            if rightCellBlock != currentBlock:
                currentBlock.neighbors.append(rightCellBlock)
            if southCellBlock != currentBlock:
                currentBlock.neighbors.append(southCellBlock)
                
        elif c.location[0] == 199 and c.location[1] == 0:
            leftCellBlock = getCell(listOfCells,c.location[0]-1, c.location[1]).block
            northCellBlock = getCell(listOfCells,c.location[0], c.location[1]+1).block
            if leftCellBlock != currentBlock:
                currentBlock.neighbors.append(leftCellBlock)
            if northCellBlock != currentBlock:
                currentBlock.neighbors.append(northCellBlock)
                
        elif c.location[0] == 0:
            rightCellBlock = getCell(listOfCells,c.location[0]+1, c.location[1]).block
            northCellBlock = getCell(listOfCells,c.location[0], c.location[1]+1).block
            southCellBlock = getCell(listOfCells,c.location[0], c.location[1]-1).block
            if rightCellBlock != currentBlock:
                currentBlock.neighbors.append(rightCellBlock)
            if northCellBlock != currentBlock:
                currentBlock.neighbors.append(northCellBlock)
            if southCellBlock != currentBlock:
                currentBlock.neighbors.append(southCellBlock)
                
        elif c.location[0] == 199:
            leftCellBlock = getCell(listOfCells,c.location[0]-1, c.location[1]).block
            northCellBlock = getCell(listOfCells,c.location[0], c.location[1]+1).block
            southCellBlock = getCell(listOfCells,c.location[0], c.location[1]-1).block
            if rightCellBlock != currentBlock:
                currentBlock.neighbors.append(rightCellBlock)
            if leftCellBlock != currentBlock:
                currentBlock.neighbors.append(leftCellBlock)
            if northCellBlock != currentBlock:
                currentBlock.neighbors.append(northCellBlock)
            if southCellBlock != currentBlock:
                currentBlock.neighbors.append(southCellBlock)
                
        elif c.location[1] == 0:
            rightCellBlock = getCell(listOfCells,c.location[0]+1, c.location[1]).block
            leftCellBlock = getCell(listOfCells,c.location[0]-1, c.location[1]).block
            northCellBlock = getCell(listOfCells,c.location[0], c.location[1]+1).block
            if rightCellBlock != currentBlock:
                currentBlock.neighbors.append(rightCellBlock)
            if leftCellBlock != currentBlock:
                currentBlock.neighbors.append(leftCellBlock)
            if northCellBlock != currentBlock:
                currentBlock.neighbors.append(northCellBlock)
                
        elif c.location[1] == 199:
            rightCellBlock = getCell(listOfCells,c.location[0]+1, c.location[1]).block
            leftCellBlock = getCell(listOfCells,c.location[0]-1, c.location[1]).block
            southCellBlock = getCell(listOfCells,c.location[0], c.location[1]-1).block
            if rightCellBlock != currentBlock:
                currentBlock.neighbors.append(rightCellBlock)
            if leftCellBlock != currentBlock:
                currentBlock.neighbors.append(leftCellBlock)
            if southCellBlock != currentBlock:
                currentBlock.neighbors.append(southCellBlock)
    
    for b in listOfBlocks:
        b.neighbors = list(dict.fromkeys(b.neighbors))
        
    file_path = constants.text_files_path + '\\blocks'
    outfile = open(file_path,'wb')
    pickle.dump(listOfBlocks,outfile)
    outfile.close()
    
    return listOfCells,listOfBlocks

# Assigns cells to their closest block
def setupBlocks(listOfCells):
    file_path = constants.text_files_path + '\\blocks'
    infile = open(file_path,'rb')
    listOfBlocks = pickle.load(infile)
    infile.close()
    
    for c in listOfCells:
        block = min(listOfBlocks,key=lambda block:dist(block.location,c.location))
        block.cells.append(c)
        c.block = block
    
    return listOfCells,listOfBlocks
