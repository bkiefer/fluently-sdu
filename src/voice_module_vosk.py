import whisper
import json
import queue
import sounddevice
from vosk import Model, KaldiRecognizer
import numpy as np

class VoiceModule():
    def __init__(self, commands: dict):
        self.model = Model("data/vosk-model-small-en-us-0.15")
        self.samplerate = 16000
        self.block_size = 16000
        self.vosk = KaldiRecognizer(self.model, self.samplerate)
        self.whisper = whisper.load_model("small")
        self.commands = commands
        self.queue = queue.Queue()
        self.stream = sounddevice.RawInputStream(
            samplerate=self.samplerate,
            blocksize=self.block_size,
            dtype='int16',
            channels=1,
            callback=self.audio_callback
        )
        self.stream.start()

    def audio_callback(self, indata, frames, time, status):
        print("audio call_back")
        if status:
            print("Audio status:", status)
        self.queue.put(bytes(indata))

    def listen_vosk(self):
        data = self.queue.get()
        sounddevice.play(np.frombuffer(data, dtype='int16'), samplerate=self.samplerate) # to listen back to what the module heard            
        if self.vosk.AcceptWaveform(data):
            result = json.loads(self.vosk.Result())
            text = result.get("text", "").lower()
            print(f"Recognized from vosk: {text}")
            for phrase, action in self.commands.items():
                if phrase in text:
                    action()
                    return
            print("No matching command.")
    
    def listen_vosk(self):
        pass
        # result = self.whisper.transcribe(data)
        # print(f"Recognized from whisper: {result}")

def say_hello():
    print("Hello")

def move_robot_home():
    print("Move robot home")

if __name__ == "__main__":
    voice_module = VoiceModule({"say hello": say_hello, "move robot home": move_robot_home})
    while True:
        voice_module.listen_vosk()