from xqtive_states import States

class XqtiveExampleStateMachine(States):
    def __init__(self):
        States.__init__(self)
        new_state_priorities = {"PowerOff": 0}
        self.state_priorities.update(new_state_priorities)

    def Message(self):
        print(f"Message {self.__dict__}")
