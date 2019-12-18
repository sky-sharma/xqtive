import os
import sys

# Get directory paths
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

# Import State Machine Class and create State Machines.  sm_defs includes "iot_brokers"
# which is the list of IoT Brokers the state machine will communicate with.  Currently "aws"
# is supported.  "mosquitto" will be added soon.  "azure" planned for future.
from xqtive_example_state_machines import ExampleController, ExampleResource
sm_defs = [
    {"sm_name": "controller", "sm_class": ExampleController, "iot_providers": ["aws_iot_mqtt"]},
    {"sm_name": "resource", "sm_class": ExampleResource}]

all_sm_queues_processes = xqtive_helpers.launch_state_machines(sm_defs, config, certs_dir)
sm_processes = all_sm_queues_processes["all_sm_processes"]

#state_machine_processes = controller_processes
# Wait till all processes have exited before killing main process
for sm_process in sm_processes:
    sm_process.join()
