from vars import constants, config
from utils import common_utils as Utils

print_type = input(f"Please insert 'all' to view logs for all EVs OR insert an number between 1 and {constants.NUMBER_OF_CARS} to view logs for a specific EV \n")
if print_type == 'all':
    config.print_logs = 0
    print('Printing in results.txt...')
    Utils.run_saev_simulation()
elif print_type.isdigit() and int(print_type) >= 1 and int(print_type) <= constants.NUMBER_OF_CARS:
    config.print_logs = print_type
    print('Printing in results.txt...')
    Utils.run_saev_simulation()
else:
    print('Invalid Input')