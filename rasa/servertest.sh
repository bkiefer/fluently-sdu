url='http://localhost:5005/model/parse'
if test -z "$input"; then
    input='set the horizontal resolution to eight'
fi
res=`curl -X POST -d "{\"text\":\"$input\"}" "$url" 2>/dev/null | tr '\n' ' '`
echo $res
