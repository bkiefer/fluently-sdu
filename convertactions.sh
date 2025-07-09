#!/bin/sh
baseonto=src/main/resources/ontology/fluently/planner.owl
defs=actiondefs.yml
java -jar actionconv/target/actionconv.jar $baseonto $defs
./ntcreate.sh
