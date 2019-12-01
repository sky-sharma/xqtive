import random
import time
from xqtive import XQtiveStateMachine

class ExampleController(XQtiveStateMachine):
    def __init__(self, sm_name, config, all_sm_queues):
        self.cust_hi_priority_states = config["states"].get("cust_hi_priority_states")
        self.actual_v = None
        #XQtiveStateMachine.__init__(self, sm_name, config, all_sm_queues)
        super().__init__(sm_name, config, all_sm_queues)

    def MESSAGE(self):
        print(f"Message {self.__dict__}")

    def PWR_SPLY_OUTPUT(self, params):
        voltage_to_set = float(params[0])
        next_states_params = [
        ["_SetCurrentLimit", 1],
        ["_SetVoltage", voltage_to_set],
        ["WAIT", "10"],
        ["_CloseContactor"]]
        self.feedback_msg = f"PWR_SPLY_OUTPUT; About to run sequence to set output voltage to {voltage_to_set}..."
        return next_states_params

    def PWR_SPLY_OFF(self):
        next_states_params = ["_SetVoltage", 0]
        self.feedback_msg = "PWR_SPLY_OFF; About to set output voltage to 0..."
        return next_states_params

    def E_STOP(self):
        next_state_params = ["_OpenContactor"]
        self.feedback_msg = "E_STOP; About to open contactor..."
        return next_state_params

    def _SetCurrentLimit(self, params):
        self.feedback_msg = f"Setting current limit to {params[0]} Amps..."

    def _SetVoltage(self, params):
        self.feedback_msg = f"Setting voltage out to {params[0]} Volts..."
        rsrc_states_queue = self.all_sm_queues["resource"]["states_queue"]
        rsrc_states_queue.put(["_SetV", str(params[0])], "substate_from_other_sm")

    def _CloseContactor(self):
        self.feedback_msg = "Closing contactor..."

    def _OpenContactor(self):
        self.feedback_msg = "Opening contactor..."

    def _ReadPollVar(self, poll_var):
        if poll_var == "VOLTS":
            return self.actual_v
        else:
            pass

    def _ActualV(self, params):
        self.actual_v = float(params[0])



class ExampleResource(XQtiveStateMachine):
    def __init__(self, sm_name, config, all_sm_queues):
        self.cust_hi_priority_states = []
        #XQtiveStateMachine.__init__(self, sm_name, config, all_sm_queues)
        super().__init__(sm_name, config, all_sm_queues)

    def _SetV(self, params):
        time.sleep(20)
        v_to_set = float(params[0])
        v_to_return = v_to_set + 5
        ctrl_states_queue = self.all_sm_queues["controller"]["states_queue"]
        ctrl_states_queue.put(["_ActualV", str(v_to_return)], "substate_from_other_sm")
