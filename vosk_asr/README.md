# Running the ASR pipeline locally on your computer

*DO NOT DO THIS IN A CONDA OR VIRTUAL ENVIRONMENT, THE PYTHON BINARY HAS TO BE THAT OF YOUR NATIVE OS INSTALLATION*

Install docker, pip, and python bindings for the gstreamer libraries

`sudo apt install docker.io docker-compose pip python3-gst-1.0`

Now install the required python packages

`pip install -r requirements.txt`

Start MQTT broker and vosk kaldi server:

`./run_compose.sh up`

Check language in `config.yml` and start ASR locally

`./mqtt_micro_asr.py config.yml`

When done, shut MQTT broker and vosk kaldi server down

`./run_compose.sh down`
