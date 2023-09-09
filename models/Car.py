from vars import constants
from utils import common_utils as Utils
from . import Charger
from vars import config

# A car transports users and travels to a CS to charge its battery    
class Car:
    def __init__(self, env, name, charge, location):
        self.env = env
        self.status = 'available'
        self.name = name
        self.charge = charge
        self.location = location
        env.process(self.checkCharge())
    
    # Car goes to charge when it's remaining charge is less than 20%
    def checkCharge(self):
        while True:
            if self.charge < constants.MAX_CHARGE * 0.2:
                self.env.process(self.chargeCar())
                yield self.env.timeout(23000)
            else:
                yield self.env.timeout(300)
    
    def chargeCar(self):
        self.status = 'busy'
        cs = Utils.get_best_score_cs(config.cs_copy, self.location, self.charge)
        time = Utils.time_taken(self.location, cs.location)
        distance = Utils.dist(self.location,cs.location)
        if config.print_logs == 0 or self.name == 'Car #' + config.print_logs:
            results_file = open(constants.file_path,"a")
            results_file.write("%s (charge %s) driving to %s at destination %s and time %d\n" % (self.name,self.charge, cs.name,cs.location,self.env.now))
            results_file.close()
        yield self.env.timeout(time)
        cs.queue += 1
        self.charge -= constants.CONSUMPTION_RATE * distance
        self.location = cs.location
        
        while True:
            myCS = 0
            for c in cs.chargers.items:
                if c.status == 'empty':
                    myCS = yield cs.chargers.get(lambda c:c.status == 'empty')
                    if type(myCS) == Charger.Charger:
                        break
            if type(myCS) != Charger.Charger:
                config.charge_wait += 60
                yield self.env.timeout(60)
            else:
                break
        
        myCS.status = 'busy' 
        chargeAmount = (constants.MAX_CHARGE-self.charge)
        chargeTime = (chargeAmount/constants.MAX_CHARGE)*constants.CHARGE_TIME
        if chargeTime + self.env.now > constants.SIM_TIME:
            cs.used += constants.SIM_TIME - self.env.now
        else:
            cs.used += chargeTime
        yield self.env.timeout(chargeTime)
        config.time_spent_charging += chargeTime
        self.charge = constants.MAX_CHARGE
        if config.print_logs == 0 or self.name == 'Car #' + config.print_logs:
            results_file = open(constants.file_path,"a")
            results_file.write("%s (charge %s) finished charging at time %d\n" % (self.name,self.charge,self.env.now))
            results_file.close()
        myCS.status = 'empty'
        yield cs.chargers.put(myCS)
        cs.queue -= 1
        self.status = 'available'
        config.num_of_charges+=1