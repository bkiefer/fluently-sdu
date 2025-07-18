import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import time

SAMPLE_RATE = 16000
DURATION = 5  # seconds
OUTPUT_FILENAME = "test.wav"

print("Loading Whisper model...")
model = whisper.load_model("small")  # options: tiny, base, small, medium, large

def record_audio():
    print(f"Recording for {DURATION} seconds...")
    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    write(OUTPUT_FILENAME, SAMPLE_RATE, audio)
    print("Recording saved.")

def transcribe_audio():
    
    print("Transcribing...")
    start = time.time()
    result = model.transcribe(OUTPUT_FILENAME)
    end = time.time()

    print(f"Time taken: {end - start:.2f} seconds")
    print(f"Transcription:\n{result['text']}")

if __name__ == "__main__":
    record_audio()
    transcribe_audio()
