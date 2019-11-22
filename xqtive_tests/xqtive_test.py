import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
xqtive_dir = f"{base_dir}/../xqtive"
xqtive_example_dir = f"{base_dir}/xqtive_example"

# Add directories to sys.path
sys.path.append(base_dir)
sys.path.append(xqtive_dir)
sys.path.append(xqtive_example_dir)

from xqtive import XqtiveStates

def test_create_custom_states():
    config = {"states":{"wait_resolution": 0.1}}

    class TestStateMachine(XqtiveStates):
        def __init__(self, config):
            self.cust_hi_priorities = {"PWR_SPLY_OUTPUT": "Normal", "PWR_SPLY_OFF": "High", "E_STOP": "Highest"}
            XqtiveStates.__init__(self, config)

    sm = TestStateMachine(config)
    return sm.hi_priorities

assert test_create_custom_states() == {"SHUTDOWN": "HIGH", "PWR_SPLY_OUTPUT": "NORMAL", "PWR_SPLY_OFF": "HIGH", "E_STOP": "HIGHEST"}
