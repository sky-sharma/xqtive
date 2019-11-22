import time
import os
import sys
import logging
import __main__

# Get main file info, and from it, site config file info
main_file_info = os.path.splitext(os.path.basename(__main__.__file__))
main_file_name = main_file_info[0]
main_file_extension = main_file_info[1]

base_dir = os.path.dirname(os.path.abspath(__main__.__file__))
xqtive_dir = f"{base_dir}/../xqtive"
modules_dir = f"{base_dir}/modules"

# Get name and path of config file
config_file_name = main_file_name + "_config.json"
config_filepath = os.path.join(base_dir, "config", config_file_name)

# Get certs dir
certs_dir = f"{base_dir}/certs"

# Add directories to sys.path
sys.path.append(xqtive_dir)
sys.path.append(modules_dir)

# Import xqtive modules
import xqtive_helpers

# Read config file
config = xqtive_helpers.read_config(config_filepath)

# Import State Machine Class and create a State Machine.
from xqtive_example_state_machine import XqtiveExampleStateMachine

state_machine_launcher_returned = xqtive_helpers.launch_state_machine(XqtiveExampleStateMachine, config, certs_dir)
state_machine_processes = state_machine_launcher_returned["processes"]

# Wait till all processes have exited before killing main process
for state_machine_process in state_machine_processes:
    state_machine_process.join()
