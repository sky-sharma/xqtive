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
            exit_state_machine = eval(f"sm.{state_to_exec}()")
        else:
            exit_state_machine = eval(f"sm.{state_to_exec}(params)")
        if exit_state_machine:
            break

def iot_read_write(obj):
    certs_dir = obj["certs_dir"]
    config = obj["config"]
    # Configure connection to IoT broker
    iot_broker = config["iot"]["broker_address"]
    iot_port = config["iot"]["broker_port"]
    subscribe_topic = config["iot"]["subscribe_topic"]
    iot_ca_cert_path = f"{certs_dir}/{config['iot']['ca_cert']}"
    iot_client_cert_path = f"{certs_dir}/{config['iot']['client_cert']}"
    iot_client_key_path = f"{certs_dir}/{config['iot']['client_key']}"
    iot_connected = False

    while True:
        if iot_connected:
            pass
        else:
            # A connection to iot is established at the beginning and if publish fails
            iot_comm = AWSIoTMQTTClient()
            iot_comm.onMessage = xqtive_helpers.iot_onmsg
            iot_comm.configureEndpoint(cloud_broker, cloud_port)
            iot_comm.configureCredentials(cloud_ca_cert_path, cloud_client_key_path, cloud_client_cert_path)
            # AWSIoTMQTTClient connection configuration
            # Not sure if the next few lines before .connect() are essential, but trying them to resolve errors causing reconnections
            #iot_comm.configureAutoReconnectBackoffTime(1, 32, 20)
            #iot_comm.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
            #iot_comm.configureDrainingFrequency(2)  # Draining: 2 Hz
            #iot_comm.configureConnectDisconnectTimeout(10)  # 10 sec
            #iot_comm.configureMQTTOperationTimeout(10)  # 10 sec
            iot_comm.connect()
            iot_comm.subscribe(cloud_device_subscribe_topic, 1, None)
            iot_connected = True

        dequeued_package = iot_queue.get()
        dequeued_package_json = json.loads(dequeued_package)
        msg_str = dequeued_package_json["msg_str"]
        msg = json.loads(msg_str)

        if (msg["action"] == "quit"):
            iot_comm.disconnect()
            iot_conected = False
            break
        else:
            topic = dequeued_package_json["topic"]
            try:
                iot_comm.publish(topic, msg_str, QoS=0)
            except:
                # If publish fails set iot_connected to false so a reconnection is attempted
                iot_comm.disconnect()
                iot_conected = False
