import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
xqtive_dir = f"{base_dir}/../xqtive"
modules_dir = f"{base_dir}/modules"
sequences_dir = f"{base_dir}/sequences"
certs_dir = f"{base_dir}/certs"

# Get name and path of config file
config_file_name = f"{os.path.splitext(__file__)[0]}_config.json"
config_filepath = os.path.join(base_dir, "config", config_file_name)

# Add directories to sys.path
sys.path.append(xqtive_dir)
sys.path.append(modules_dir)

# Import xqtive modules
import xqtive_helpers

# Read config file; add sequences_dir to config dict
config = xqtive_helpers.read_config(config_filepath)
config["sequences_dir"] = sequences_dir

# Import State Machine Class and create State Machines.
from xqtive_example_state_machines import ExampleController, ExampleResource
all_sm_names_classes = [
    {"sm_name": "controller", "sm_class": ExampleController},
    {"sm_name": "resource", "sm_class": ExampleResource}]

all_sm_queues_processes = xqtive_helpers.launch_all_state_machines(all_sm_names_classes, config, certs_dir, dependents=["resource"])
sm_processes = all_sm_queues_processes["all_sm_processes"]

#state_machine_processes = controller_processes
# Wait till all processes have exited before killing main process
for sm_process in sm_processes:
    sm_process.join()
