import whisper
import json
import queue
import sounddevice
from vosk import Model, KaldiRecognizer
import numpy as np
from collections import deque

class VoiceModule():
    def __init__(self, commands: dict):
        self.samplerate = 16000
        self.block_size = 8000
        self.queue = queue.Queue()
        self.buffer_size = self.samplerate * 2
        self.buffer = deque(maxlen=self.buffer_size)
        
        self.model = Model("data/vosk-model-small-en-us-0.15")
        self.vosk = KaldiRecognizer(self.model, self.samplerate)
        self.whisper = whisper.load_model("small")

        self.commands = commands
        
        self.stream = sounddevice.RawInputStream(
            samplerate=self.samplerate,
            blocksize=self.block_size,
            dtype='int16',
            channels=1,
            callback=self.audio_callback
        )
        self.stream.start()

    def audio_callback(self, indata, frames, time, status):
        if status:
            print("Audio status:", status)
        self.queue.put(bytes(indata))
        self.buffer.extend(np.frombuffer(indata, dtype=np.int16))

    def listen_vosk(self):
        data = self.queue.get()
        sounddevice.play(np.frombuffer(data, dtype='int16'), samplerate=self.samplerate) # to listen back to what the module heard            
        if self.vosk.AcceptWaveform(data):
            result = json.loads(self.vosk.Result())
            text = result.get("text", "").lower()
            print(f"Recognized from vosk: {text}")
            self._handle_commands(text=text)
    
    def listen_whisper(self):
        if len(self.buffer) < self.buffer_size:
            return
        audio_np = np.array(self.buffer, dtype=np.float32) / 32768.0
        sounddevice.play((audio_np * 32768).astype(np.int16), samplerate=self.samplerate) # to listen back top what the module heard
        sounddevice.wait() # the play is non-blocking, the buffer is always 2 seconds (with vosk is real time) so we need this wait to listen back
        result = self.whisper.transcribe(audio_np, fp16=False)
        text = result.get("text", "").lower()
        print(f"Recognized from whisper: {text}")
        self._handle_commands(text=text)

    def _handle_commands(self, text):
        for phrase, action in self.commands.items():
            if phrase in text:
                action()
                return
        print("No matching command.")

def say_hello():
    print("Hello")

def move_robot_home():
    print("Move robot home")

if __name__ == "__main__":
    voice_module = VoiceModule({"say hello": say_hello, "move robot home": move_robot_home})
    while True:
        # voice_module.listen_vosk()
        voice_module.listen_whisper()