from xqtive import XqtiveStates

class XqtiveExampleStateMachine(XqtiveStates):
    def __init__(self, config):
        self.cust_hi_priority_states = ["PWR_SPLY_OFF","E_STOP"]
        XqtiveStates.__init__(self, config)

    def MESSAGE(self):
        print(f"Message {self.__dict__}")

    def PWR_SPLY_OUTPUT(self, params):
        voltage_to_set = float(params[0])
        next_states_params = [
        ["SetCurrentLimit", 1],
        ["SetVoltage", voltage_to_set],
        ["WAIT", "20"],
        ["CloseContactor"]]
        self.feedback_msg = f"PWR_SPLY_OUTPUT; About to run sequence to set output voltage to {voltage_to_set}..."
        return next_states_params

    def PWR_SPLY_OFF(self):
        next_states_params = ["SetVoltage", 0]
        self.feedback_msg = "PWR_SPLY_OFF; About to set output voltage to 0..."
        return next_states_params

    def E_STOP(self):
        next_state_params = ["OpenContactor"]
        self.feedback_msg = "E_STOP; About to open contactor..."
        return next_state_params

    def SetCurrentLimit(self, params):
        self.feedback_msg = f"Setting current limit to {params[0]} Amps..."

    def SetVoltage(self, params):
        self.feedback_msg = f"Setting voltage out to {params[0]} Volts..."

    def CloseContactor(self):
        self.feedback_msg = "Closing contactor..."

    def OpenContactor(self):
        self.feedback_msg = "Opening contactor..."
