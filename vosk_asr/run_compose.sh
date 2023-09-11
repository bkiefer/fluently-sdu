#!/bin/bash
#set -x
cd `dirname $0`
export LANG=`grep 'language *:' config.yml | sed 's/language *: *//'`
cmd="$1"
if test -z "$cmd"; then
    cmd="up"
fi
if `type -all docker-compose | grep -q 'not found'` ; then
    docker compose "$cmd"
else
    docker-compose "$cmd"
fi
