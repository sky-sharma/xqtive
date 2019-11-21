import json
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT

def read_config(config_filepath):
    with open(config_filepath) as cfgFile:
        config = json.load(cfgFile)
    return(config)

def iot_onmsg(msg):
    msg_payload = msg.payload
    dict_payload = json.loads(msg_payload)
    msg = dict_payload["message"]
    print(msg)
    msg_array = msg.split(";")

    # Capitalize state: all states called from the outside have to be public.
    # Public states are indicated by being named all upper case
    msg_arr_with_cap_state = [msg_array[0].upper()] + msg_array[1:]
    states_queue.put(msg_arr_with_cap_state)

def iot_connect(obj):
    certs_dir = obj["certs_dir"]
    global states_queue
    states_queue = obj["states_queue"]
    config = obj["config"]
    # Configure connection to IoT broker
    iot_broker = config["iot"]["broker_address"]
    iot_port = config["iot"]["broker_port"]
    subscribe_topic = config["iot"]["subscribe_topic"]
    iot_ca_cert_path = f"{certs_dir}/{config['iot']['ca_cert']}"
    iot_client_cert_path = f"{certs_dir}/{config['iot']['client_cert']}"
    iot_client_key_path = f"{certs_dir}/{config['iot']['client_key']}"

    # A connection to iot is established at the beginning and if publish fails
    iot_comm = AWSIoTMQTTClient("xqtive")
    iot_comm.onMessage = iot_onmsg
    iot_comm.configureEndpoint(iot_broker, iot_port)
    iot_comm.configureCredentials(iot_ca_cert_path, iot_client_key_path, iot_client_cert_path)
    iot_comm.connect()
    iot_comm.subscribe(subscribe_topic, 1, None)
    return iot_comm

def iot_close(iot_comm):
    iot_comm.disconnect()
