# Prerequisites for installation (tested on Ubuntu 22.04 [Mate])

```
sudo apt install python3-gst-1.0 libgirepository1.0-dev libcairo2-dev python3-pip espeak

pip install -r requirements.txt
```

To download the TTS model, do

```
tts --text 'This is a test.' --model_name 'tts_models/en/ljspeech/tacotron2-DDC'
```

This will generate a wav file that can be played to check if it works.

# Running the server

Start your favorite MQTT broker first. Then:

    python3 tts-server.py

Send this message to `tts/behaviour`, e.g., with MQTT-Explorer

    { "id": 222, "text": "This i a text that does not make any sense" }

The server currently uses the default pulseaudio output device.
