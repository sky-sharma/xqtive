import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
xqtive_dir = f"{base_dir}/../xqtive"
xqtive_example_dir = f"{base_dir}/xqtive_example"

# Add directories to sys.path
sys.path.append(base_dir)
sys.path.append(xqtive_dir)
sys.path.append(xqtive_example_dir)

from xqtive import XQtiveStates

def _create_state_machine():
    config = {"states":{"wait_resolution": 0.1}}
    class TestStateMachine(XQtiveStates):
        def __init__(self, config):
            self.cust_hi_priority_states = ["PWR_SPLY_OFF", "E_STOP"]
            XQtiveStates.__init__(self, config)
    return TestStateMachine(config)

def test_create_custom_states():
    """
    Test that hi_priority_states from customer specified test machine classes
    are merged with existing hi_priority_states.
    """
    sm = _create_state_machine()
    return set(sm.hi_priority_states)

def test_POLL_1():
    """
    Test that POLL attributes are set correctly. Also check for
    capitalization of Type (param[1]) and comparison (param[3])
    """
    sm = _create_state_machine()
    params = ["20", "flOAt", "AI0", "aBoVe", "17"]
    sm.POLL(params)
    returned = {}
    returned["poll_var"] = sm.__dict__["poll_var"]
    returned["poll_comparison"] = sm.__dict__["poll_comparison"]
    returned["poll_match"] = sm.__dict__["poll_match"]
    returned["poll_lo_thresh"] = sm.__dict__["poll_lo_thresh"]
    returned["poll_hi_thresh"] = sm.__dict__["poll_hi_thresh"]
    return returned

def test_POLL_2():
    """
    Test that POLL attributes are set correctly. Also check for
    1. Capitalization of Type (param[1]) and comparison (param[3])
    2. Proper ordering of hi_thresh and lo_thresh
    """
    sm = _create_state_machine()
    params = ["20", "iNt", "DWORD_1", "bEtWeEn", "15", "3"]
    sm.POLL(params)
    returned = {}
    returned["poll_var"] = sm.__dict__["poll_var"]
    returned["poll_comparison"] = sm.__dict__["poll_comparison"]
    returned["poll_match"] = sm.__dict__["poll_match"]
    returned["poll_lo_thresh"] = sm.__dict__["poll_lo_thresh"]
    returned["poll_hi_thresh"] = sm.__dict__["poll_hi_thresh"]
    return returned

def test_POLL_3():
    """
    Test that POLL attributes are set correctly. Also check for
    1. Capitalization of Type (param[1]) and comparison (param[3])
    2. Proper ordering of hi_thresh and lo_thresh
    """
    sm = _create_state_machine()
    params = ["20", "float", "AI1", "bEtWeEn", "5.7", "19.4"]
    sm.POLL(params)
    returned = {}
    returned["poll_var"] = sm.__dict__["poll_var"]
    returned["poll_comparison"] = sm.__dict__["poll_comparison"]
    returned["poll_match"] = sm.__dict__["poll_match"]
    returned["poll_lo_thresh"] = sm.__dict__["poll_lo_thresh"]
    returned["poll_hi_thresh"] = sm.__dict__["poll_hi_thresh"]
    return returned

def test_POLL_4():
    """
    Test that POLL attributes are set correctly. Also check for
    capitalization of Type (param[1]) and comparison (param[3])
    """
    sm = _create_state_machine()
    params = ["20", "Int", "DWORD_2", "mAtCh", "14"]
    sm.POLL(params)
    returned = {}
    returned["poll_var"] = sm.__dict__["poll_var"]
    returned["poll_comparison"] = sm.__dict__["poll_comparison"]
    returned["poll_match"] = sm.__dict__["poll_match"]
    returned["poll_lo_thresh"] = sm.__dict__["poll_lo_thresh"]
    returned["poll_hi_thresh"] = sm.__dict__["poll_hi_thresh"]
    return returned

assert test_create_custom_states() == set(["SHUTDOWN", "PWR_SPLY_OFF", "E_STOP"])
assert test_POLL_1() == {"poll_var": "AI0", "poll_comparison": "ABOVE", "poll_match": None, "poll_lo_thresh": 17.0, "poll_hi_thresh": None}
assert test_POLL_2() == {"poll_var": "DWORD_1", "poll_comparison": "BETWEEN", "poll_match": None, "poll_lo_thresh": 3, "poll_hi_thresh": 15}
assert test_POLL_3() == {"poll_var": "AI1", "poll_comparison": "BETWEEN", "poll_match": None, "poll_lo_thresh": 5.7, "poll_hi_thresh": 19.4}
assert test_POLL_4() == {"poll_var": "DWORD_2", "poll_comparison": "MATCH", "poll_match": 14, "poll_lo_thresh": None, "poll_hi_thresh": None}
