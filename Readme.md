# Purpose

This module handles the natural language interaction part of the Fluently Scanning use case.

# Installation

## Prerequisites

Tested on Ubuntu 22.04

You need python3 and the mosquitto package installed.

## rasa NLU

Go to the `rasa` folder and follow the readme to train a model based on the training data in the `data` folder.

## vosk ASR

Go to the `vosk_asr` folder. The Readme there contains instructions for the installation of some python prerequisites, and how to run it.

## coqui AI TTS

Go to the tts folder. The Readme there contains instructions for the installation of some python prerequisites, and how to run it.

In the top level directory, call

    ./compile
    mvn install

Now the agent that ties everything together is ready to go:

    ./run.sh
