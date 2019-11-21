import xqtive_helpers

def state_machine(object):
    sm = object["state_machine"]
    states_queue = object["states_queue"]
    while True:
        # Get dict containing both the state to execute and parameters needed by that state.
        # Then separate the state to execute from the parameters.
        state_and_params = states_queue.get()    # Get highest priority item without priority number
        print(f" got: {state_and_params}")
        state_to_exec = state_and_params[0]
        params = state_and_params[1:]    # params may be missing depending on the type of state
        # Run the state using the parameters and decide if the state machine is to continue running or not.
        # NONE of the states return anything EXCEPT the "Shutdown" state which returns a True
        if params == []:
            returned = eval(f"sm.{state_to_exec}()")
        else:
            returned = eval(f"sm.{state_to_exec}(params)")
        if returned != None:
            if returned == "SHUTDOWN":
                # If a True was returned then the SHUTDOWN state was the last to run
                break
            elif type(returned).__name__ == "list":
                # If a list of states was returned, enqueue them
                for state_and_params in returned:
                    states_queue.put(state_and_params, use_last_state_priority=True)
