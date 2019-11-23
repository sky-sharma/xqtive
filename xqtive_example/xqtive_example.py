import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
xqtive_dir = f"{base_dir}/../xqtive"
modules_dir = f"{base_dir}/modules"
certs_dir = f"{base_dir}/certs"

# Get name and path of config file
config_file_name = f"{os.path.splitext(__file__)[0]}_config.json"
config_filepath = os.path.join(base_dir, "config", config_file_name)

# Add directories to sys.path
sys.path.append(xqtive_dir)
sys.path.append(modules_dir)

# Import xqtive modules
import xqtive_helpers

# Read config file
config = xqtive_helpers.read_config(config_filepath)

# Import State Machine Class and create a State Machine.
from xqtive_example_state_machine import XQtiveExampleStateMachine

state_machine_launcher_returned = xqtive_helpers.launch_state_machine(XQtiveExampleStateMachine, config, certs_dir)
state_machine_processes = state_machine_launcher_returned["processes"]

# Wait till all processes have exited before killing main process
for state_machine_process in state_machine_processes:
    state_machine_process.join()
