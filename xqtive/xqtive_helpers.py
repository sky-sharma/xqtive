import os
import json
import time
import logging
import xqtive
from queue import Queue
from multiprocessing import Process
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT

def read_config(config_filepath):
    """
    Read config JSON file and return as managed dict
    """
    with open(config_filepath) as cfgFile:
        config = json.load(cfgFile)
    return(config)


def state_params_str_to_array(state_params_str):
    """
    Take a ';' separated state_params_str and return a state_params_array with capitalized state
    """
    state_and_params = state_params_str.split(";")

    # Trim whitespace from both ends of states, params
    state_and_params_stripped = []
    for element in state_and_params:
        state_and_params_stripped.append(element.strip())

    # Capitalize state: all states called from the outside have to be public.
    # Public states are indicated by being named all upper case
    state_and_params_with_cap_state = [state_and_params_stripped[0].upper()] + state_and_params_stripped[1:]
    return state_and_params_with_cap_state


def get_sequence_names(config):
    sequence_names = []
    sequence_names += [filename for filename in os.listdir(config["sequences_dir"]) if filename.endswith(".seq")]
    return sequence_names


def read_sequence_file(sequence_filepath):
    """
    Read a sequence file and convert to states_and_params list of lists
    """
    seq_file = open(sequence_filepath, "r")
    state_params_strs = seq_file.readlines()
    states_and_params = []
    for state_params_str in state_params_strs:
        if state_params_str in ["\r", "\n", "\r\n"] or state_params_str.startswith("//"):    # Ignore blank and comment lines (start with '//')
            pass
        else:
            state_and_params = state_params_str_to_array(state_params_str)
            states_and_params.append(state_and_params)
    return states_and_params


def iot_onmsg(msg):
    try:
        msg_payload = msg.payload
        dict_payload = json.loads(msg_payload)
        type = dict_payload["type"].strip().lower()    # Remove whitespace from both ends and make lower-case
        value = dict_payload["value"].strip()
        if type == "run_sequence":
            states_and_params = read_sequence_file(f"{config['sequences_dir']}/{value}.seq")
            for state_and_params in states_and_params:
                states_queue.put(state_and_params, "from_sequence")
        elif type == "run_state":
            state_and_params = state_params_str_to_array(value)
            states_queue.put(state_and_params, "from_iot")
    except Exception as e:
        iot_rw_logger.error(f"ERROR; iot_onmsg; {e}")


def iot_rw(obj):
    sm_name = obj.get("sm_name")
    certs_dir = obj.get("certs_dir")
    global states_queue
    all_sm_queues = obj.get("all_sm_queues")
    this_sm_queues = all_sm_queues[sm_name]
    states_queue = this_sm_queues["states_queue"]
    iot_rw_queue = this_sm_queues["iot_rw_queue"]
    global config
    config = obj.get("config")
    #dependents = obj.get("dependents")
    process_name = f"{sm_name}_iot_rw"
    global iot_rw_logger
    iot_rw_logger = create_logger(process_name, config)
    try:
        # Configure connection to IoT broker
        iot_broker = config["iot"]["broker_address"]
        iot_port = config["iot"]["broker_port"]
        subscribe_topic = f"{config['iot']['subscribe_topic_prefix']}/{sm_name}"
        #dependent_topics = []
        #for dependent in dependents:
        #    dependent_topics.append(f"{config['iot']['subscribe_topic_prefix']}/{dependent}")
        publish_topic = config["iot"]["publish_topic"]
        iot_ca_cert_path = f"{certs_dir}/{config['iot']['ca_cert']}"
        iot_client_cert_path = f"{certs_dir}/{config['iot']['client_cert']}"
        iot_client_key_path = f"{certs_dir}/{config['iot']['client_key']}"
    except Exception as e:
        iot_rw_logger.error(f"ERROR; {process_name}; {type(e).__name__}; {e}")

    iot_connected = False
    while True:
        try:
            if not iot_connected:
                try:
                    # A connection to iot is established at the beginning and if publish fails
                    iot_comm = AWSIoTMQTTClient(f"{sm_name}_xqtive")
                    iot_comm.onMessage = iot_onmsg
                    iot_comm.configureEndpoint(iot_broker, iot_port)
                    iot_comm.configureCredentials(iot_ca_cert_path, iot_client_key_path, iot_client_cert_path)
                    iot_comm.connect()
                    iot_comm.subscribe(subscribe_topic, 1, None)
                    iot_connected = True
                except Exception as e:
                    # If there was an error during connection close and wait before trying again
                    iot_comm.close()
                    time.sleep(config["iot"]["wait_between_reconn_attempts"])
            else:
                dequeued = iot_rw_queue.get()
                if dequeued == "SHUTDOWN":
                    # Send SHUTDOWN to topics of dependents, then exit
                    #msg_dict = {"type": "run_state", "value": "SHUTDOWN"}
                    #msg_str = json.dumps(msg_dict)
                    #for dependent_topic in dependent_topics:
                    #    iot_comm.publish(dependent_topic, msg_str, QoS=1)
                    break
                else:
                    type = dequeued["type"]
                    msg_dict = dequeued
                    msg_str = json.dumps(msg_dict)
                    iot_comm.publish(publish_topic, msg_str, QoS=1)
        except Exception as e:
            iot_rw_logger.error(f"ERROR; {process_name}; {type(e).__name__}; {e}")


def iot_close(iot_comm):
    iot_comm.disconnect()


def create_logger(logger_name, config):
    logging.basicConfig(filename=f"/var/log/{logger_name}.log", format="%(asctime)s %(message)s", level=config["log_level"])
    logger = logging.getLogger(logger_name)
    return logger


def launch_state_machines(sm_defs, config, certs_dir):
    all_sm_queues = {}
    for sm_def in sm_defs:
        sm_name = sm_def["sm_name"]
        uses_iot = sm_def["uses_iot"]
        sm_queues = create_sm_queues(config, uses_iot)
        all_sm_queues[sm_name] = sm_queues
    all_sm = {}
    for sm_def in sm_defs:
        sm_name = sm_def["sm_name"]
        sm_class = sm_def["sm_class"]
        sm = create_sm(config, sm_def, all_sm_queues)
        all_sm[sm_name] = sm
    all_sm_processes = []
    for sm_def in sm_defs:
        sm_name = sm_def["sm_name"]
        uses_iot = sm_def["uses_iot"]
        sm = all_sm[sm_name]
        sm_processes = launch_sm_processes(sm_name, sm, uses_iot, all_sm_queues, config, certs_dir)
        all_sm_processes += sm_processes
    to_return = {"all_sm_queues": all_sm_queues, "all_sm": all_sm, "all_sm_processes": all_sm_processes}
    return to_return

def create_sm_queues(config, uses_iot):
    # Create managed PriorityQueue for states
    states_queue = xqtive.XQtiveQueue(config)

    if uses_iot:
        # Create managed queue for sending messages to process that writes to IoT
        xqtive.XQtiveSyncMgr.register("Queue", Queue)
        iot_rw_queue_mgr = xqtive.XQtiveSyncMgr()
        iot_rw_queue_mgr.start()
        iot_rw_queue = iot_rw_queue_mgr.Queue()
    else:
        iot_rw_queue = None

    sm_queues = {"states_queue": states_queue, "iot_rw_queue": iot_rw_queue}
    return sm_queues

def create_sm(config, sm_def, all_sm_queues):
    sm_name = sm_def["sm_name"]
    sm_class = sm_def["sm_class"]
    sm = sm_class(sm_name, config, all_sm_queues)
    return sm

def launch_sm_processes(sm_name, sm, uses_iot, all_sm_queues, config, certs_dir):
    launched_processes = []

    if uses_iot:
        # Launch IoT process which receives messages to publish to IoT
        iot_rw_cfg = {
            "sm_name": sm_name,
            "certs_dir": certs_dir,
            "all_sm_queues": all_sm_queues,
            "config": config}
        iot_rw_process = Process(target = iot_rw, args = [iot_rw_cfg])
        iot_rw_process.start()
        launched_processes.append(iot_rw_process)

    # Launch sm process
    sm_cfg = {
        "sm_name": sm_name,
        "sm": sm,
        "config": config,
        "all_sm_queues": all_sm_queues}
    sm_process = Process(target = xqtive.xqtive_state_machine, args = [sm_cfg])
    sm_process.start()
    launched_processes.append(sm_process)
    return launched_processes
