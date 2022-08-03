'''
Created on Dec 27, 2019
 
@author: Ahmed Shaker
'''

from simulation.bss import init_bss_phase
from simulation.bss import saev_bss_simulation
from simulation.cs import init_cs_phase
from simulation.cs import saev_cs_simulation

simType = input("Run the Battery Swapping Station simulation (1) or the Charging Station simulation (2)\n")
if simType == '1':
    runGeneration =  input("Run BSS generation (1) or use previously generated BSSs (2)\n")
    withRelocation = input("Would you like to enable the relocation algorithm? (y or n)\n")
    if runGeneration == '1':
        init_bss_phase.runBSSGenerationPhase()
    if withRelocation == 'y':
        if runGeneration == '1':
            saev_bss_simulation.runSAEVSimulation(True,True)
        else:
            saev_bss_simulation.runSAEVSimulation(True,False)
    else:
        saev_bss_simulation.runSAEVSimulation(False,False)
elif simType == '2':
    runGeneration =  input("Run CS generation (1) or use previously generated CSs (2)\n")
    if runGeneration == '1':
        init_cs_phase.runCSGenerationPhase()
    saev_cs_simulation.runSAEVSimulation()
else:
    print('Please enter "1" or "2"')
    