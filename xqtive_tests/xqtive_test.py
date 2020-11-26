import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
xqtive_dir = f"{base_dir}/../xqtive"
xqtive_example_dir = f"{base_dir}/xqtive_example"

# Add directories to sys.path
sys.path.append(base_dir)
sys.path.append(xqtive_dir)
sys.path.append(xqtive_example_dir)

from xqtive import XQtiveStateMachine

def _create_state_machine():
    config = {"states": {"normal_priority": 0, "hi_priority_states": ["PWR_SPLY_OFF", "E_STOP"]}}
    class TestStateMachine(XQtiveStateMachine):
        def __init__(self, sm_name, config, all_sm_queues):
            XQtiveStateMachine.__init__(self, sm_name, config, all_sm_queues)
    return TestStateMachine("", config, {})

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

assert test_POLL_1() == {"poll_var": "AI0", "poll_comparison": "ABOVE", "poll_match": None, "poll_lo_thresh": 17.0, "poll_hi_thresh": None}
assert test_POLL_2() == {"poll_var": "DWORD_1", "poll_comparison": "BETWEEN", "poll_match": None, "poll_lo_thresh": 3, "poll_hi_thresh": 15}
assert test_POLL_3() == {"poll_var": "AI1", "poll_comparison": "BETWEEN", "poll_match": None, "poll_lo_thresh": 5.7, "poll_hi_thresh": 19.4}
assert test_POLL_4() == {"poll_var": "DWORD_2", "poll_comparison": "MATCH", "poll_match": 14, "poll_lo_thresh": None, "poll_hi_thresh": None}
