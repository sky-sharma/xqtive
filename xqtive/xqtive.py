# xqtive.py
import time
import xqtive_helpers
from queue import PriorityQueue
from multiprocessing.managers import SyncManager

# Create XqtiveSyncMgr
class XqtiveSyncMgr(SyncManager):
    pass

class XqtiveStates(object):
    """
    This class defines a generic state machine. Each method is a state.
    Child classes can be created which extend or override these states.
    States named in all caps are public (can be called from outside). States
    not named in all caps are private (can only be called by other states)
    """

    def __init__(self, config):
        """
        Defines private data that all states share
        """
        self.feedback_msg = None
        self.priority_values = {"HIGH": 0, "NORMAL": config["states"].get("normal_priority", 999999)}
        self.hi_priority_states = ["SHUTDOWN"]
        try:
            # See if there are any custom hi_priority states
            if self.cust_hi_priority_states == None:
                self.cust_hi_priority_states = {}
        except:
            self.cust_hi_priority_states = {}

        # Make sure all priority entries are upper case
        #cust_hi_priorities.update((key, val.upper()) for key, val in cust_hi_priorities.items())

        # Merge existing hi_priority_states with custom ones
        hi_priority_states = set(self.hi_priority_states)
        cust_hi_priority_states = set(self.cust_hi_priority_states)
        self.hi_priority_states = list(hi_priority_states | cust_hi_priority_states)

        # wait_resolution is the minimum amount of sleep time
        # while executing a Wait. Needed to avoid hogging the CPU.
        # If one is not provided in the config, use default
        default_wait_resolution = 0.1
        states_cfg = config.get("states")
        if states_cfg != None:
            self.wait_resolution = states_cfg.get("wait_resolution", default_wait_resolution)
        else:
            self.wait_resolution = default_wait_resolution

    def SLEEP(self, params):
        """
        Blocking wait using time.sleep
        Format: SLEEP;10
        """
        time.sleep(float(params[0]))

    def WAIT(self, params):
        """
        Non-blocking wait. Achieved by offloading to WaitUntilDeadline state
        Format: WAIT;10
        """
        self.wait_deadline = time.time() + float(params[0])
        next_states = [["WaitUntil"]]    # Send as list of lists
        return next_states

    def WaitUntil(self):
        """
        Offloaded from WAIT state. We keep coming back to this state until
        a deadline is reached. Can be preempted by hi_priority_state (e.g. SHUTDOWN)
        """
        if time.time() >= self.wait_deadline:
            # Waiting is done
            self.wait_deadline = 0
        else:
            time.sleep(self.wait_resolution)
            next_states_params = [["WaitUntil"]]    # Send as list of lists
            return next_states_params

    def POLL(self, params):
        """
        Non-blocking state that allows polling a variable until a time-limit is
        reached OR the variable meets a comparison criterion.
        Format: POLL;FLOAT;ANALOG_IN_0;20;ABOVE;30
        """
        type = params[0].upper()    # INT, FLOAT, BOOL, STR
        self.poll_var = params[1]
        self.poll_time_limit = float(params[2])    # seconds
        self.poll_comparison = params[3].upper()    # MATCH, ABOVE, BELOW, BETWEEN
        if self.poll_comparison == "MATCH":
            if type == "INT":
                self.poll_match = int(params[4])
            elif type == "FLOAT":
                self.poll_match = float(params[4])
            elif type == "BOOL":
                self.poll_match = bool(params[4])
            elif type == "STR":
                self.poll_match = params[4]
        elif self.poll_comparison == "ABOVE":
            if type == "INT":
                self.poll_lo_thresh = int(params[4])
            elif type == "FLOAT":
                self.poll_lo_thresh = float(params[4])
        elif self.poll_comparison == "BELOW":
            if type == "INT":
                self.poll_hi_thresh = int(params[4])
            elif type == "FLOAT":
                self.poll_hi_thresh = float(params[4])
        elif self.poll_comparison == "BETWEEN":
            if type == "INT":
                self.poll_hi_thresh = max(int(params[4]), int(params[5]))
                self.poll_lo_thresh = min(int(params[4]), int(params[5]))
            elif type == "FLOAT":
                self.poll_hi_thresh = max(float(params[4]), float(params[5]))
                self.poll_lo_thresh = min(float(params[4]), float(params[5]))


    def SHUTDOWN(self):
        return "SHUTDOWN"


class XqtiveQueue():
    """
    A class that takes care of putting / getting unique items in a PriorityQueue.
    The class wraps the functionality of including a priority with the put item AND
    it takes care of adding a unique count as the second element in the three-element tuple
    to break any ties between multiple items with the same priority. This is because we DON'T
    want comparisons between the actual items in case the priorities are the same.
    """
    def __init__(self, priority_values, hi_priority_states):
        """
        Create managed Priority queue shared between processes
        """
        XqtiveSyncMgr.register("PriorityQueue", PriorityQueue)
        states_queue_mgr = XqtiveSyncMgr()
        states_queue_mgr.start()

        self.queue = states_queue_mgr.PriorityQueue()
        self.put_count = 0
        self.priority_values = priority_values

        # All predefined priorities are ABOVE normal.
        self.hi_priority_states = hi_priority_states

    def put(self, state_and_params, **optional):
        # If state_to_exec is one of the ones in self.priority_per_state then retrieve
        # corresponding priority. Otherwise priority is normal_state_priority.
        state_to_exec = state_and_params[0]

        # See if state to put is a "substate" which means the priority should be
        # one less than the superstate that called it. If the state is NOT a substate
        # Check if it is a hi_priority_state and send the corresponding priority (= 0).
        # Else send NORMAL priority.
        substate_flag = optional.get("substate")
        if substate_flag == None:
            if state_to_exec in self.hi_priority_states:
                priority_to_use = self.priority_values["HIGH"]
            else:
                priority_to_use = self.priority_values["NORMAL"]
        elif substate_flag == True:
            if self.last_state_priority > 0:
                priority_to_use = self.last_state_priority - 1
            else:
                priority_to_use = self.last_state_priority
        else:
            priority_to_use = self.last_state_priority

        self.put_count += 1
        self.queue.put((priority_to_use, self.put_count, state_and_params))

    def get(self):
        gotten_item = self.queue.get()
        self.last_state_priority = gotten_item[0]
        gotten_item_data = gotten_item[2]    # Skip element 1 which is put_count

        # If gotten item is of High (0) then none of the other items already in the queue are to be handled. So Flush queue.
        if self.last_state_priority == 0:
            while not self.queue.empty():
                try:
                    self.queue.get(False)
                except Exception as e:
                    if e.__str__ == "Empty":
                        # If queue is empty exit this while loop
                        continue
                self.queue.task_done()
        return gotten_item_data


def xqtive_state_machine(object):
    sm = object.get("state_machine")
    states_queue = object.get("states_queue")
    iot_rw_queue = object.get("iot_rw_queue")
    config = object.get("config")
    process_name = "xqtive_state_machine"
    xqtive_state_machine_logger = xqtive_helpers.create_logger(process_name, config)
    while True:
        try:
            # Get dict containing both the state to execute and parameters needed by that state.
            # Then separate the state to execute from the parameters.
            state_and_params = states_queue.get()    # Get highest priority item without priority number
            state_to_exec = state_and_params[0]
            params = state_and_params[1:]    # params may be missing depending on the type of state
            # Run the state using the parameters and decide if the state machine is to continue running or not.
            # NONE of the states return anything EXCEPT the "Shutdown" state which returns a True
            # Send info. about states being run to IoT except for some states that are called repeatedly
            if state_to_exec not in ["WaitUntil", "PollUntil"]:
                iot_rw_queue.put(state_and_params)
            if params == []:
                returned = eval(f"sm.{state_to_exec}()")
            else:
                returned = eval(f"sm.{state_to_exec}(params)")

            # If a state placed a feedback message to publish, then publish it and clear out the message
            if sm.feedback_msg != None:
                iot_rw_queue.put(sm.feedback_msg)
                sm.feedback_msg = None

            if returned != None:
                if returned == "SHUTDOWN":
                    # If SHUTDOWN received then SHUTDOWN state was the last to run
                    iot_rw_queue.put("SHUTDOWN")
                    break
                elif type(returned).__name__ == "list":
                    if type(returned[0]).__name__ == "list":
                        # If returned contains list of lists. We need to reverse that list
                        # because dequeueing happens in descending order of put_count
                        next_states_params = returned
                    else:
                        # If returned does not contain list of lists, it probably contains only one list.
                        # Turn that into list of lists to be consistent
                        next_states_params = [returned]
                    # If a list of states_params was returned, by last state, then enqueue them with
                    # one priority level higher (i.e. subtract 1) than super-state
                    for state_and_params in next_states_params:
                        next_state_to_exec = state_and_params[0]

                        # Set substate flag to True unless next state is a repeat of this one and is a "WaitUntil" or "PollUntil".
                        # If the substate flag is True then the next state will be enqueued at a higher priority
                        # than the last one. Else the next state is enqueued at the same priority as the last one.
                        if next_state_to_exec == state_to_exec and next_state_to_exec in ["WaitUntil", "PollUntil"]:
                            substate_flag = False
                        else:
                            substate_flag = True
                        states_queue.put(state_and_params, substate=substate_flag)
        except Exception as e:
            xqtive_state_machine_logger.error(f"ERROR; {process_name}; {type(e).__name__}; {e}")
            pass
