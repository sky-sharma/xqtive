# xqtive.py
import time
import xqtive_helpers
from queue import PriorityQueue
from multiprocessing.managers import SyncManager


class XQtiveSyncMgr(SyncManager):
    """
    XQtiveSyncMgr
    """
    pass


class XQtiveStateMachine(object):
    """
    This class defines a generic state machine. Each method is a state.
    Child classes can be created which extend or override these states.
    States named in all caps are public (can be called from outside). States
    not named in all caps are private (can only be called by other states)
    """

    def __init__(self, sm_name, config, all_sm_queues):
        """
        Defines private data that all states share
        """
        self.sm_name = sm_name
        self.feedback_msg = None
        self.poll_lo_thresh = None
        self.poll_hi_thresh = None
        self.poll_match = None
        self.priority_values = {"HIGH": 0, "NORMAL": config["states"].get("normal_priority", 999999)}
        self.hi_priority_states = config["states"].get("hi_priority_states")
        self.all_sm_queues = all_sm_queues
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

        # sleep_time (the minimum amount of time to sleep per call to this state)
        # is needed to avoid hogging the CPU. If one is not provided in the config, use default
        default_sleep_time = 0.1
        states_cfg = config.get("states")
        if states_cfg != None:
            self.sleep_time = states_cfg.get("sleep_time", default_sleep_time)
        else:
            self.sleep_time = default_sleep_time

    def _set_other_sm_queues(self, other_sm_queues):
        self.other_sm_queues = other_sm_queues

    def SLEEP(self, params):
        """
        Blocking wait using time.sleep
        Format: SLEEP;10
        """
        time.sleep(float(params[0]))

    def WAIT(self, params):
        """
        Non-blocking wait. Achieved by offloading to _WaitUntil state
        Format: WAIT;10
        """
        self.wait_deadline = time.time() + float(params[0])
        next_states = [["_WaitUntil"]]    # Send as list of lists
        return next_states

    def _WaitUntil(self):
        """
        Offloaded from WAIT state. Keep coming back to this state (i.e. non-blocking) until
        a deadline is reached. Can be preempted by hi_priority_state (e.g. SHUTDOWN)
        """
        if time.time() >= self.wait_deadline:
            # Waiting is done
            self.wait_deadline = 0
        else:
            time.sleep(self.sleep_time)
            next_states_params = [["_WaitUntil"]]    # Send as list of lists
            return next_states_params

    def POLL(self, params):
        """
        Non-blocking state that allows polling a variable until a time-limit is
        reached OR the variable meets a comparison criterion.
        Format example 1: POLL;20;FLOAT;ANALOG_IN_0;ABOVE;30
        Format example 2: POLL;30;INT;DIG_WORD;BETWEEN;4;739
        """
        self.poll_deadline = time.time() + float(params[0])    # seconds
        param_type = params[1].upper()    # INT, FLOAT, BOOL, STR
        self.poll_var = params[2]
        self.poll_comparison = params[3].upper()    # MATCH, ABOVE, BELOW, BETWEEN
        if self.poll_comparison == "MATCH":
            if param_type == "INT":
                self.poll_match = int(params[4])
            elif param_type == "FLOAT":
                self.poll_match = float(params[4])
            elif param_type == "BOOL":
                self.poll_match = bool(params[4])
            elif param_type == "STR":
                self.poll_match = params[4]
            else:
                print(f"Unsupported param_type for '{self.poll_comparison}' comparison: {param_type}")
        elif self.poll_comparison == "ABOVE":
            if param_type == "INT":
                self.poll_lo_thresh = int(params[4])
            elif param_type == "FLOAT":
                self.poll_lo_thresh = float(params[4])
            else:
                print(f"Unsupported param_type for '{self.poll_comparison}' comparison: {param_type}")
        elif self.poll_comparison == "BELOW":
            if param_type == "INT":
                self.poll_hi_thresh = int(params[4])
            elif param_type == "FLOAT":
                self.poll_hi_thresh = float(params[4])
            else:
                print(f"Unsupported param_type for '{self.poll_comparison}' comparison: {param_type}")
        elif self.poll_comparison == "BETWEEN":
            if param_type == "INT":
                self.poll_hi_thresh = max(int(params[4]), int(params[5]))
                self.poll_lo_thresh = min(int(params[4]), int(params[5]))
            elif param_type == "FLOAT":
                self.poll_hi_thresh = max(float(params[4]), float(params[5]))
                self.poll_lo_thresh = min(float(params[4]), float(params[5]))
            else:
                print(f"Unsupported param_type for '{self.poll_comparison}' comparison: {param_type}")
        else:
            print(f"Unsupported comparison: {self.poll_comparison}")
        next_states_params = [["_PollUntil"]]    # Send as list of lists
        return next_states_params

    def _PollUntil(self):
        """
        Offloaded from POLL state. Keep coming back to this state (i.e. non-blocking) until
        a deadline is reached or a polled value satisfies a comparison criterion.
        Can be preempted by hi_priority_state (e.g. SHUTDOWN)
        """
        qual_str = f"comparison: {self.poll_comparison}; match: {self.poll_match}; lo_thresh: {self.poll_lo_thresh}; hi_thresh: {self.poll_hi_thresh}"
        if time.time() >= self.poll_deadline:
            # Waiting is done
            self.poll_deadline = 0
            self.feedback_msg = f"Poll failed. Time Limit Reached. '{self.poll_var}' value: {self.poll_value}; {qual_str}"
        else:
            # Check if polled var has satisfied criterion
            self.poll_value = self._ReadPollVar(self.poll_var)
            if self.poll_value != None:
                if self.poll_comparison == "ABOVE":
                    criterion_satisfied = self.poll_value > self.poll_lo_thresh
                elif self.poll_comparison == "BELOW":
                    criterion_satisfied = self.poll_value < self.poll_hi_thresh
                elif self.poll_comparison == "BETWEEN":
                    criterion_satisfied = self.poll_lo_thresh <= self.poll_value <= self.poll_hi_thresh
            else:
                criterion_satisfied = False

            if criterion_satisfied:
                self.feedback_msg = f"Poll succeeded. '{self.poll_var}' value: {self.poll_value}; {qual_str}"
            else:
                time.sleep(self.sleep_time)
                next_states_params = [["_PollUntil"]]    # Send as list of lists
                return next_states_params

    def _ReadPollVar(poll_var):
        pass

    def SHUTDOWN(self):
        # Send SHUTDOWN messages to all other State Machine queues
        self.all_sm_queues.pop(self.sm_name)
        try:
            for sm_queues in list(self.all_sm_queues.values()):
                sm_queues["states_queue"].put(["SHUTDOWN"], "from_other_sm")
        except:
            # We're passing on errors here because the state_machine we are trying to stop may already have stopped
            pass
        return "SHUTDOWN"


class XQtiveQueue():
    """
    A class that takes care of putting / getting unique items in a PriorityQueue.
    The class wraps the functionality of including a priority with the put item AND
    it takes care of adding a unique count as the second element in the three-element tuple
    to break any ties between multiple items with the same priority. This is because we DON'T
    want comparisons between the actual items in case the priorities are the same.
    """
    def __init__(self, config):
        """
        Create managed Priority queue shared between processes
        """
        XQtiveSyncMgr.register("PriorityQueue", PriorityQueue)
        states_queue_mgr = XQtiveSyncMgr()
        states_queue_mgr.start()

        self.queue = states_queue_mgr.PriorityQueue()
        self.put_count = 0
        self.priority_values = {"HIGH": 0, "NORMAL": config["states"].get("normal_priority", 999999)}
        self.last_state_priority = self.priority_values["NORMAL"]

        # All predefined priorities are ABOVE normal.
        self.hi_priority_states = config["states"].get("hi_priority_states")
        self.cust_hi_priority_states = config["states"].get("cust_hi_priority_states")
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

    def put(self, state_and_params, priority_qual):
        """
        The state about to be enqueued will be given a priority depending on
        (1) where it was requested from and (2) whether it is designated as a
        hi_priority state.  The priority_qual defines these criteria.  These are the meanings
        of priority_qual:
        1. "from_sequence": the state originated in a sequence file, so enqueue it with NORMAL
        priority EVEN if it is designated as hi_priority. Otherwise a state in the middle of a
        sequence file could invalidate the rest of the sequence file.
        2. "from_iot": the state originated from the cloud (IoT). If it is a designated hi_priority state
        enqueue it with HIGH priority, otherwise with NORMAL priority.
        3. "from_other_sm": Same as 2 above.
        4. "sub_state": the state about to be enqueued is a sub_state of the caller state. If the
        sub_state is designated as hi_priority then enqueue it with HIGH priority, which invalidates
        all other states in the queue. Otherwise enqueue it with a higher priority than the caller state
        (i.e. subtract 1 from priority of caller state), unless caller is already at HIGH priority.
        5. "repeated_wait_poll": states "_WaitUntil" and "_PollUntil" are unique in that they call themselves
        until condition(s) are met. If one of these calls itself, then we set the priority of the called to the
        same as the caller state UNLESS the caller state's.
        """
        state_to_exec = state_and_params[0]

        if priority_qual == "from_sequence":
            priority_to_use = self.priority_values["NORMAL"]
        elif priority_qual in ["from_iot", "from_other_sm"]:
            if state_to_exec in self.hi_priority_states:
                priority_to_use = self.priority_values["HIGH"]
            else:
                priority_to_use = self.priority_values["NORMAL"]
        elif priority_qual in ["sub_state", "from_other_sm_sub_state"]:
            if state_to_exec in self.hi_priority_states:
                priority_to_use = self.priority_values["HIGH"]
            elif self.last_state_priority > 0:
                priority_to_use = self.last_state_priority - 1
            else:
                priority_to_use = self.last_state_priority
        elif priority_qual == "repeated_wait_poll":
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


def xqtive_state_machine(obj):
    sm_name = obj.get("sm_name")
    sm = obj.get("sm")
    all_sm_queues = obj.get("all_sm_queues")
    this_sm_queues = all_sm_queues[sm_name]
    #sm = this_sm_and_queues["sm"]
    states_queue = this_sm_queues["states_queue"]
    iot_rw_queue = this_sm_queues["iot_rw_queue"]
    config = obj.get("config")
    process_name = f"{sm_name}_xqtive_sm"
    xqtive_sm_logger = xqtive_helpers.create_logger(process_name, config)
    sequence_names = xqtive_helpers.get_sequence_names(config)
    if iot_rw_queue != None:
        iot_rw_queue.put({"sender": sm_name,"msg_type": "sequence_names", "value": sequence_names})
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
            if state_to_exec not in ["_WaitUntil", "_PollUntil"] and iot_rw_queue != None:
                iot_rw_queue.put({"sender": sm_name, "msg_type": "state_to_run", "value": state_and_params})
            if params == []:
                returned = eval(f"sm.{state_to_exec}()")
            else:
                returned = eval(f"sm.{state_to_exec}(params)")

            # If a state placed a feedback message to publish, then publish it and clear out the message
            if sm.feedback_msg != None:
                if iot_rw_queue != None:
                    iot_rw_queue.put({"sender": sm_name, "msg_type": "state_feedback", "value": sm.feedback_msg})
                sm.feedback_msg = None

            if returned != None:
                if returned == "SHUTDOWN":
                    # If SHUTDOWN received then SHUTDOWN state was the last to run
                    if iot_rw_queue != None:
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

                        # Set priority_qual "sub_state" unless next state is a repeat of this one and is a "_WaitUntil" or "_PollUntil".
                        # If the priority_qual flag is True then the next state will be enqueued at a higher priority
                        # than the last one. Else the next state is enqueued at the same priority as the last one.
                        if next_state_to_exec == state_to_exec and next_state_to_exec in ["_WaitUntil", "_PollUntil"]:
                            priority_qual = "repeated_wait_poll"
                        else:
                            priority_qual = "sub_state"
                        states_queue.put(state_and_params, priority_qual)
        except Exception as e:
            xqtive_sm_logger.error(f"ERROR; {process_name}; {type(e).__name__}; {e}")
            pass
