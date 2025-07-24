#!/bin/bash
when=$(date -Iseconds)
java -jar fluently_sdu_nlu.jar -c config.yml | tee logs/nlu${when}.log
