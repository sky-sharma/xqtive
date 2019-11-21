import time
import os
import sys
import logging
import __main__
from multiprocessing import Process

# Get current file name
current_file_info = os.path.splitext(os.path.basename(__file__))
current_file_name = current_file_info[0]
current_file_extension = current_file_info[1]

# Get main file info, and from it, site config file info
main_file_info = os.path.splitext(os.path.basename(__main__.__file__))
main_file_name = main_file_info[0]
main_file_extension = main_file_info[1]

# If running .py files
if main_file_extension == ".py":
    base_dir = os.path.dirname(os.path.abspath(__main__.__file__))
    xqtive_dir = f"{base_dir}/../_reuse/xqtive"
    modules_dir = f"{base_dir}/modules"

# If running .pyc file
if main_file_extension == ".pyc":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__main__.__file__)))
    xqtive_dir = f"{base_dir}/../_reuse/xqtive/__pycache__"
    modules_dir = f"{base_dir}/modules/__pycache__"

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
import xqtive_processes

# Read config file
config = xqtive_helpers.read_config(config_filepath)

# Import State Machine Class and create a State Machine.
from xqtive_example_state_machine import XqtiveExampleStateMachine
sm = XqtiveExampleStateMachine(config)

# Create managed PriorityQueue for states
states_queue = xqtive_helpers.StatesQueue(sm.hi_priorities, config["states"]["normal_priority"])

spawned_processes = []

state_machine_cfg = {"state_machine": sm, "states_queue": states_queue}
state_machine_process = Process(target = xqtive_processes.state_machine, args = [state_machine_cfg])
state_machine_process.start()
spawned_processes.append(state_machine_process)

#states_queue.put(["Wait", "3"])
#states_queue.put(["Wait", "2"])
#states_queue.put(["Wait", "1"])
#states_queue.put(["Message"])
iot_connect_cfg = {"certs_dir": certs_dir, "states_queue": states_queue, "config": config}
iot_comm = xqtive_helpers.iot_connect(iot_connect_cfg)

# Wait till all processes have exited before killing main process
for spawned_process in spawned_processes:
    spawned_process.join()

xqtive_helpers.iot_close(iot_comm)