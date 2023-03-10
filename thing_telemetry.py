from awscrt import io, http, auth
from awscrt import mqtt5, exceptions
from awsiot import mqtt_connection_builder, mqtt5_client_builder
from concurrent.futures import Future
import time

thing_endpoint = "a2hcchteq9ar5b-ats.iot.eu-central-1.amazonaws.com" #double check this is created
port = None
cert_filepath = "/workspaces/cubanops/test_thing_1/example_1/ro-virtual-thing-1.cert.pem"
pri_key = "/workspaces/cubanops/test_thing_1/example_1/ro-virtual-thing-1.private.key"
ca_path = "/workspaces/cubanops/test_thing_1/example_1/root-CA.crt"

received_count = 0
TIMEOUT = 100
topic_filter = "test/topic"
future_stopped = Future()
future_connection_success = Future()
client_id = "basicPubSub"
message_topic = "/test/topic"
message_string = "Hello from virtual thing"

# Callback when any publish is received
def on_publish_received(publish_packet_data):
    publish_packet = publish_packet_data.publish_packet
    assert isinstance(publish_packet, mqtt5.PublishPacket)
    print("Received message from topic'{}':{}".format(publish_packet.topic, publish_packet.payload))
    global received_count
    received_count += 1
    print("received count {}".format(received_count))

# Callback for the lifecycle event Stopped
def on_lifecycle_stopped(lifecycle_stopped_data: mqtt5.LifecycleStoppedData):
    print("Lifecycle Stopped")
    global future_stopped
    future_stopped.set_result(lifecycle_stopped_data)

def on_lifecycle_connection_success(lifecycle_connect_success_data: mqtt5.LifecycleConnectSuccessData):
    print("Lifecycle Connection Success")
    global future_connection_success
    future_connection_success.set_result(lifecycle_connect_success_data)

# Callback for the lifecycle event Connection Failure
def on_lifecycle_connection_failure(lifecycle_connection_failure: mqtt5.LifecycleConnectFailureData):
    print("Lifecycle Connection Failure")
    print("Connection failed with exception:{}".format(lifecycle_connection_failure.exception))

def on_lifecycle_disconnect(lifecycle_disconnect_data: mqtt5.LifecycleDisconnectData):
    print("Lifecycle Connection Failure")
    print("Connection failed with exception:{}".format(lifecycle_disconnect_data.exception))

client =  mqtt5_client_builder.mtls_from_path(
            endpoint = thing_endpoint,
            port = port,
            cert_filepath = cert_filepath,
            pri_key_filepath= pri_key,
            ca_filepath=ca_path,
            http_proxy_options=None,
            on_publish_received=on_publish_received,
            on_lifecycle_stopped=on_lifecycle_stopped,
            on_lifecycle_attempting_connect= None,
            on_lifecycle_connection_success=on_lifecycle_connection_success,
            on_lifecycle_connection_failure=on_lifecycle_connection_failure,
            on_lifecycle_disconnection=on_lifecycle_disconnect,
            client_id=client_id)

print("MQTT5 Client Created")
client.start()
lifecycle_connect_success_data = future_connection_success.result()

print("Subscribing to topic '{}'...".format(message_topic))
subscribe_future = client.subscribe(subscribe_packet=mqtt5.SubscribePacket(
        subscriptions=[mqtt5.Subscription(
            topic_filter=message_topic,
            qos=mqtt5.QoS.AT_LEAST_ONCE)]))
suback = subscribe_future.result(TIMEOUT)
print("Subscribed with {}".format(suback.reason_codes))

publish_count = 1
while (publish_count):
    message = "{} [{}]".format(message_string, publish_count)
    print("Publishing message to topic '{}': {}".format(message_topic, message))
    publish_future = client.publish(mqtt5.PublishPacket(
        topic=message_topic,
        payload=message_string,
        qos=mqtt5.QoS.AT_LEAST_ONCE
    ))
    time.sleep(1)
    publish_count = publish_count + 1 
    publish_completion_data = publish_future.result(TIMEOUT)

    
