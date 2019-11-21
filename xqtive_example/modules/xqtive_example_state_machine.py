from xqtive_states import States

class XqtiveExampleStateMachine(States):
    def __init__(self, config):
        States.__init__(self, config)
        new_state_priorities = {"PowerOff": 0}
        self.hi_priorities.update(new_state_priorities)

    def Message(self):
        print(f"Message {self.__dict__}")
