dir=`dirname $(realpath "$0")`
if test -f "logback.xml"; then
    lb="-Dlogback.configurationFile=logback.xml"
fi
java -jar $lb "$dir"/target/fluently_sdu_nlu.jar "$@"
