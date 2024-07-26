# An ASR client using a vosk server sending output to MQTT

*DO NOT RUN THIS IN A CONDA OR VIRTUAL ENVIRONMENT WITH SEPARATE PYTHON BINARY, THE PYTHON BINARY HAS TO BE THAT OF YOUR NATIVE OS INSTALLATION*

Install python bindings for the gstreamer libraries

```
sudo apt install libgirepository1.0-dev python3-gst-1.0 libcairo2-dev python3-pip


pip install -r requirements.txt
```

Start MQTT broker and vosk kaldi server:

`./run_compose.sh up`

Check language in `config.yml` and start ASR locally

`./mqtt_micro_asr.py config.yml`

When done, shut MQTT broker and vosk kaldi server down

`./run_compose.sh down`
