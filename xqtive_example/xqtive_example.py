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

# Create controller state_machine and queues
ctrl_sm_queues_returned = xqtive_helpers.create_state_machine_and_queues("controller", ExampleController, config)

# Create resource state_machine and queues
rsrc_sm_queues_returned = xqtive_helpers.create_state_machine_and_queues("resource", ExampleResource, config)

all_state_machines_queues = {"controller": ctrl_sm_queues_returned, "resource": rsrc_sm_queues_returned}

# Launch Controller State Machine
controller_processes = xqtive_helpers.launch_state_machine("controller", all_state_machines_queues, config, certs_dir, dependents=["resource"])
#controller_processes = ctrl_launcher_returned["processes"]
#controller_queue = ctrl_launcher_returned["states_queue"]

# Launch resource state machine
resource_processes = xqtive_helpers.launch_state_machine("resource", all_state_machines_queues, config, certs_dir)
#resource_processes = resource_launcher_returned["processes"]
#resource_queue = resource_launcher_returned["states_queue"]

state_machine_processes = controller_processes + resource_processes

# Put all_state_queues in shared place
#all_state_queues = {"controller": controller_queue, "resource": resource_queue}
#config["all_state_queues"] = all_state_queues

#state_machine_processes = controller_processes
# Wait till all processes have exited before killing main process
for state_machine_process in state_machine_processes:
    state_machine_process.join()
