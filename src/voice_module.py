import whisper
import json
import queue
import sounddevice
import vosk
import numpy as np
from collections import deque
from gubokit import utilities

class VoiceModule():
    def __init__(self, commands: dict, verbose=False):
        console_level = 'debug' if verbose else 'info'
        self.logger = utilities.CustomLogger("Voice", "MeMVoice.log", console_level=console_level, file_level=None)
        self.samplerate = 16000
        self.block_size = 8000
        self.queue = queue.Queue()
        self.buffer_size = self.samplerate * 2
        self.buffer = deque(maxlen=self.buffer_size)
        vosk.SetLogLevel(-1)
        self.model = vosk.Model("data/vosk-model-small-en-us-0.15")
        self.vosk = vosk.KaldiRecognizer(self.model, self.samplerate)
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
            self.logger.warning("Audio status:", status)
        self.queue.put(bytes(indata))
        self.buffer.extend(np.frombuffer(indata, dtype=np.int16))

    def listen_vosk(self):
        fnc_executed, text = False, ""
        data = self.queue.get()
        sounddevice.play(np.frombuffer(data, dtype='int16'), samplerate=self.samplerate) # to listen back to what the module heard            
        if self.vosk.AcceptWaveform(data):
            result = json.loads(self.vosk.Result())
            text = result.get("text", "").lower()
            self.logger.debug(f"Recognized from vosk: {text}")
            fnc_executed = self._handle_commands(text=text)
        return fnc_executed, text
    
    def listen_whisper(self):
        fnc_executed, text = False, ""
        if len(self.buffer) >= self.buffer_size:
            audio_np = np.array(self.buffer, dtype=np.float32) / 32768.0
            sounddevice.play((audio_np * 32768).astype(np.int16), samplerate=self.samplerate) # to listen back top what the module heard
            sounddevice.wait() # the play is non-blocking, the buffer is always 2 seconds (with vosk is real time) so we need this wait to listen back
            result = self.whisper.transcribe(audio_np, fp16=False)
            # self.logger.debug(result)
            if len(result.get('segments')) > 0:
                no_speech_prob = result.get('segments')[0].get("no_speech_prob", 1)
                self.logger.debug(no_speech_prob)
                if no_speech_prob < 0.6:
                    text = result.get("text", "").lower()
                    self.logger.debug(f"Recognized from whisper: {text}")
                    fnc_executed = self._handle_commands(text=text)
        return fnc_executed, text

    def _handle_commands(self, text):
        for phrase, action in self.commands.items():
            if phrase in text:
                action()
                return True
        return False

def say_hello():
    print("Hello")

def move_robot_home():
    print("Move robot home")

if __name__ == "__main__":
    voice_module = VoiceModule({"say hello": say_hello, "move robot home": move_robot_home}, verbose=True)
    while True:
        voice_module.listen_vosk()
        # voice_module.listen_whisper()