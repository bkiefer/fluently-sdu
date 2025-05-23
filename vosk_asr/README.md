# An ASR client using a vosk recognizer, sending output to MQTT

This has been tested on Ubuntu 22.04. Dependencies might differ for other distros.

*DO NOT RUN THIS IN A CONDA OR VIRTUAL ENVIRONMENT WITH SEPARATE PYTHON BINARY, THE PYTHON BINARY HAS TO BE THAT OF YOUR NATIVE OS INSTALLATION*

Install python bindings for the gstreamer libraries, the mosquitto system service, and the python requirements

```
sudo apt install libgirepository1.0-dev python3-gst-1.0 libcairo2-dev python3-pip mosquitto


pip install -r requirements.txt
```

Download the silero VAD model

    wget https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.jit

and the ASR model of your choice, at https://alphacephei.com/vosk/models

Adapt the config.yml to your needs (let `model_path` point to the directory where your unpacked ASR model is)

Start the recognizer:

    ./run_asr.sh

Currently, the recognizer uses the default pulseaudio input device, you should even be able to switch it when the recognizer is running. If you want something more sophisticated, you may have to modify the gstreamer pipeline (the defaults are in gstmicpipeline.py) to your needs, you don't have to modify the code, you can specify it as `pipeline` key in the config.

The ASR result will be send to the `voskasr/asrresult/<lang>` MQTT topic.
