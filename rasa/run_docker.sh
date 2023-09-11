dockerid=`docker run -d -p5005:5005 fluently_sdu`
while test -z ""; do
    docker logs "$dockerid" 2>&1 | grep -q 'up and running' &&
        echo "Rasa server is up and running" && exit 0;
    sleep 5
done
