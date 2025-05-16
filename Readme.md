# Purpose

This module handles the natural language interaction part of the Fluently Scanning use case.

# Installation

## Prerequisites

Tested on Ubuntu 22.04

On Ubuntu:
python3, mosquitto, openjdk-11-jdk (at least), docker, nvidia-container-toolkit (for use of GPU, optional)

## rasa NLU

Go to the `rasa` folder and follow the readme to train a model based on the training data in the `data` folder:

`./rasadock train` to train, `./rasadock` to run the container for inference

## vosk ASR

Go to the `vosk_asr` folder. The Readme there contains instructions for the installation of some python prerequisites, and how to run it.

## coqui AI TTS

Go to the tts folder. The Readme there contains instructions for the installation of some python prerequisites, and how to run it.

In the top level directory, call

    mvn install

Now the agent that ties everything together is ready to go:

    ./run.sh
