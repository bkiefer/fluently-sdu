import paho.mqtt.client as mqtt
import json
from gubokit import utilities

class FluentlyMQTTClient:
    def __init__(self, client_id: str, topic="nlu/intent", broker: str = "localhost", port: int = 1883, verbose=False):
        console_level = 'debug' if verbose else 'info'
        self.logger = utilities.CustomLogger("Voice", "MeMVoice.log", console_level=console_level, file_level=None)
        self.client = mqtt.Client(client_id=client_id)
        self.broker = broker
        self.port = port
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.message_callback = None
        self.connect()
        self.start()
        self.subscribe(topic)
        self.intent = []
        self.state = 1
        self.command_given = False

    def on_connect(self, client, userdata, flags, rc):
        self.logger.info(f"Connected with result code {rc}")

    def on_message(self, client, userdata, msg):
        message = msg.payload.decode()
        topic = msg.topic
        self.logger.debug(f"Received message on topic '{topic}': {message}")
        self.intent.append(message)
        if self.message_callback:
            self.message_callback(topic, message)

    def connect(self):
        self.client.connect(self.broker, self.port, keepalive=60)

    def start(self):
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic: str):
        self.client.subscribe(topic)
        self.logger.info(f"Subscribed to topic '{topic}'")

    def publish(self, message_: str):
        topic = "tts/behaviour"
        message ={  "id": "fluently",
            "text": message_,
            "motion": "",
            "delay": 0}
        try:
            json_message = json.dumps(message)
            self.client.publish(topic, json_message)
            self.logger.debug(message_)
        except (TypeError, ValueError) as e:
            self.logger.debug(f"Failed to serialize message to JSON: {e}")

    def set_message_callback(self, callback):
        self.message_callback = callback

    def get_intent(self):
        # print(self.intent)
        if len(self.intent) >=1:
            ans = self.intent[-1]
            self.intent = []
            return ans
        else:
            return None
        
    def clear_intents(self):
        self.intent.clear()