# Purpose

This module handles the natural language interaction part of the Fluently Engine assembly use case

# Installation

## Prerequisites

Tested on Ubuntu 22.04

You need python3, docker and docker compose installed.

## rasa NLU

Go to the `rasa` folder and follow the readme to train a model based on the training data in the `data` folder.

## vosk ASR

Go to the `vosk_asr` folder. The Readme there contains instructions for the installation of some python prerequisites. Once these are installed and the rasa training is done, you can start the whole pipeline with `run.sh`

`run.sh` starts two things that can also be easily started on their own, e.g., for debugging: `./run_compose.sh`, which starts the MQTT broker, the ASR and the NLU server, and `python3 micro_asr_rasa.py config.yml`, which picks up the audio from the input device, sends it to the ASR, and the ASR results to the NLU.

The pipeline uses MQTT to send the ASR and NLU results. The broker is started with the `docker compose up` inside the `run_compose.sh` that is called from `run.sh`, and can be reached on port 1883. If that port is taken on your machine, change the `docker-compose.yml` in the `vosk_asr` folder accordingly.

MQTT clients are available for almost all programming languages. The topics used are `voskasr/asrresult/en` and `voskasr/nlu/en`, respectively.

To check, if the pipeline works, you can user MQTT explorer (http://mqtt-explorer.com/), and connect it to the broker on localhost. It will display all topics where new messages are sent.

One more issue that might need configuration is the audio input. Set the device that you want to use as your default linux audio input device in the 'Sound Settings'. If the ASR is not working at all, or only very badly, check the sample rate of the device and change it accordingly in the `config.yml` before you restart the `micro_asr_rasa.py config.yml`
