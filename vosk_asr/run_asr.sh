#!/bin/bash
scrdir=`dirname $(realpath $0)`
cd $scrdir
python mqtt_micro_vadasr.py config.yml
