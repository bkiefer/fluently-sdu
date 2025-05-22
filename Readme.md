# Purpose

This module handles the natural language interaction part of the Fluently Scanning and MEM use case.

# Installation

Clone fluently-sdu like this:

    git clone https://github.com/bkiefer/fluently-sdu.git
    cd fluently-sdu
    git submodule update --init --recursive
    git submodule update --recursive --remote

## Prerequisites

Tested on Ubuntu 22.04

Packages to install on Ubuntu:
python3 (installed by default), mosquitto, openjdk-11-jdk (at least)

Install docker: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04

Install nvidia-container-toolkit, for use of GPU (optional): https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

Remember to follow the ‘Configuring docker’ steps!


Install Vonda: https://github.com/bkiefer/vonda , check possibly additional prerequisites in the `ReadMe.md` after cloning the repository!

    git clone https://github.com/bkiefer/vonda.git
    cd vonda
    mvn install

Link vondac symbolically to the home folder of fluently-sdu

    cd ../fluently-sdu
    ln -s ../vonda/bin/vondac

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
