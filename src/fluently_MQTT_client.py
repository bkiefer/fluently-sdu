class FluentlyMQTTClient:
    def __init__(self, client_id: str, broker: str = "localhost", port: int = 1883):
        self.client = mqtt.Client(client_id=client_id)
        self.broker = broker
        self.port = port
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.message_callback = None
        self.connect()
        self.start()
        self.subscribe("nlu/intent")
        self.intent = []
        self.state = 1
        self.command_given = False

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")

    def on_message(self, client, userdata, msg):
        message = msg.payload.decode()
        topic = msg.topic
        print(f"Received message on topic '{topic}': {message}")
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
        print(f"Subscribed to topic '{topic}'")

    def publish(self, message_: str):
        topic = "tts/behaviour"
        message ={  "id": "fluently",
            "text": message_,
            "motion": "",
            "delay": 0}
        try:
            json_message = json.dumps(message)
            self.client.publish(topic, json_message)
            print(message_)
        except (TypeError, ValueError) as e:
            print(f"Failed to serialize message to JSON: {e}")

    def set_message_callback(self, callback):
        self.message_callback = callback

    def get_intent(self):
        if len(self.intent) >=1:
            ans = self.intent[-1]
            self.intent = []
            return ans
        else:
            return None
        
    def clear_intents(self):
        self.intent.clear()
