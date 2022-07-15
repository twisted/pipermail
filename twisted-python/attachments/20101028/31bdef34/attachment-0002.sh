./test_producer.py one &
./test_producer.py two &
./test_producer.py three &
sleep 3
#dd if=/dev/zero bs=1024 count=157286400000 | nc localhost 8080 > /dev/null 
# echo 'please type asdfasdfasdf and press enter within 5 seconds'
nc localhost 8080 #> /dev/null 