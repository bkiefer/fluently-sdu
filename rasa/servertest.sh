url='http://localhost:5005/model/parse'
if test -z "$input"; then
    input='spring zu kapitel sieben'
fi
res=`curl -X POST -d "{\"text\":\"$input\"}" "$url" 2>/dev/null | tr '\n' ' '`
echo $res
