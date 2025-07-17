# vosk_command_listener.py
import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# 1. Define your command functions
def move_robot_home():
    print("Robot moving to home position.")

def shutdown_robot():
    print("Shutting down robot.")

def say_hello():
    print("Hello there!")

# 2. Define command dictionary
COMMANDS = {
    "move the robot to home position": move_robot_home,
    "shut down the robot": shutdown_robot,
    "say hello": say_hello,
}

# 3. Load Vosk model
# model = Model("data/vosk-model-en-us-0.22-lgraph")
model = Model("data/vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model, 16000)

# 4. Create audio queue
q = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print("Audio status:", status)
    q.put(bytes(indata))

# 5. Main loop
def listen_and_execute():
    print("Listening... Speak a command.")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()
                print(f"Recognized: {text}")
                for phrase, action in COMMANDS.items():
                    if phrase in text:
                        action()
                        return
                print("No matching command.")

if __name__ == "__main__":
    while True:
        listen_and_execute()