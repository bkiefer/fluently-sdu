#!/bin/bash
scdir=`dirname $0`
cd "$scdir"
./run_compose.sh &
python3 micro_asr_rasa.py config.yml
