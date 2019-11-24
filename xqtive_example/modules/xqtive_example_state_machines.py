import random
import time
from xqtive import XQtiveStateMachine

class ExampleController(XQtiveStateMachine):
    def __init__(self, config, all_sm_queues):
        self.cust_hi_priority_states = config["states"].get("cust_hi_priority_states")
        XQtiveStateMachine.__init__(self, config, all_sm_queues)

    def MESSAGE(self):
        print(f"Message {self.__dict__}")

    def PWR_SPLY_OUTPUT(self, params):
        voltage_to_set = float(params[0])
        next_states_params = [
        ["_SetCurrentLimit", 1],
        ["_SetVoltage", voltage_to_set],
        ["WAIT", "20"],
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

    def _CloseContactor(self):
        self.feedback_msg = "Closing contactor..."

    def _OpenContactor(self):
        self.feedback_msg = "Opening contactor..."

    def _ReadPollVar(self, poll_var):
        if poll_var == "NOW_SEC":
            return (time.time() % 60)    # Seconds now
        else:
            return (random.random() * 100)

class ExampleResource(XQtiveStateMachine):
    def __init__(self, config, all_sm_queues):
        self.cust_hi_priority_states = []
        XQtiveStateMachine.__init__(self, config, all_sm_queues)

    def EXEC_CMD(self, params):
        print(f"Params {params}")
