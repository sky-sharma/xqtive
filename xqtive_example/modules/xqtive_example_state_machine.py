from xqtive_states import States

class XqtiveExampleStateMachine(States):
    def __init__(self, config):
        self.cust_hi_priorities = {"PWR_SPLY_OFF": 0}
        States.__init__(self, config)

    def MESSAGE(self):
        print(f"Message {self.__dict__}")

    def PWR_SPLY_OUTPUT(self, params):
        voltage_to_set = float(params[0])
        next_states_params = [
        ["SetCurrentLimit", 1],
        ["SetVoltage", voltage_to_set],
        ["WAIT", "20"],
        ["CloseContactor"]]
        return next_states_params

    def PWR_SPLY_OFF(self):
        print("Turning off power!")

    def SetCurrentLimit(self, params):
        print(f"Setting current limit to {params[0]} Amps.")

    def SetVoltage(self, params):
        print(f"Setting voltage out to {params[0]} Volts.")

    def CloseContactor(self):
        print(f"Closing contactor.")
