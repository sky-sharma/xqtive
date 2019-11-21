from xqtive import XqtiveStates

class XqtiveExampleStateMachine(XqtiveStates):
    def __init__(self, config):
        self.cust_hi_priorities = {"PWR_SPLY_OUTPUT": "Normal", "PWR_SPLY_OFF": "High", "E_STOP": "Highest"}
        XqtiveStates.__init__(self, config)

    def MESSAGE(self):
        print(f"Message {self.__dict__}")

    def PWR_SPLY_OUTPUT(self, params):
        voltage_to_set = float(params[0])
        print(f"Setting output voltage to {voltage_to_set}")
        next_states_params = [
        ["SetCurrentLimit", 1],
        ["SetVoltage", voltage_to_set],
        ["WAIT", "20"],
        ["CloseContactor"]]
        return next_states_params

    def PWR_SPLY_OFF(self):
        print("Turning off power!")
        next_states_params = [
        ["SetVoltage", 0],
        ["WAIT", "5"],
        ["OpenContactor"]]
        return next_states_params

    def E_STOP(self):
        print("Hitting E-Stop!")
        next_state_params = ["OpenContactor"]
        return next_state_params

    def SetCurrentLimit(self, params):
        print(f"Setting current limit to {params[0]} Amps.")

    def SetVoltage(self, params):
        print(f"Setting voltage out to {params[0]} Volts.")

    def CloseContactor(self):
        print(f"Closing contactor.")

    def OpenContactor(self):
        print(f"Opening contactor.")
