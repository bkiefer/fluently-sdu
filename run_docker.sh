#!/bin/sh

cd "`dirname $0`"

docker run --rm --name fluently_mem_nlu -d \
       -v ./docker_config.yml:/app/config.yml \
       -v ./logs/:/app/logs \
       --add-host host.docker.internal=host-gateway \
       fluently_nlu
