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

# Launch Controller State Machine
ctrl_launcher_returned = xqtive_helpers.launch_state_machine("controller", ExampleController, config, certs_dir, dependents=["resource"])
controller_processes = ctrl_launcher_returned["processes"]
controller_sm = ctrl_launcher_returned["state_machine"]
controller_queue = ctrl_launcher_returned["states_queue"]

# Launch resource state machine
resource_launcher_returned = xqtive_helpers.launch_state_machine("resource", ExampleResource, config, certs_dir)
resource_processes = resource_launcher_returned["processes"]
resource_sm = resource_launcher_returned["state_machine"]
resource_queue = resource_launcher_returned["states_queue"]

state_machine_processes = controller_processes + resource_processes

# Exchange queues
controller_sm._set_other_sm_queues([resource_queue])
resource_sm._set_other_sm_queues([controller_queue])

#state_machine_processes = controller_processes
# Wait till all processes have exited before killing main process
for state_machine_process in state_machine_processes:
    state_machine_process.join()
