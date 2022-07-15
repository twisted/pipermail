import time, psyco
from twisted.spread import banana
PSYCO = 1
if PSYCO:
    psyco.bind(banana.encode)
    psyco.bind(banana.int2b128)
    psyco.bind(banana.b1282int)
    psyco.bind(banana.decode)
    psyco.bind(banana.Banana.dataReceived)
    psyco.bind(banana.Banana._encode)

s = banana.encode([1, 2, "hello", "there"])
banana.decode(s)

if PSYCO:
    print "Psyco on"
else:
    print "Psyco off"

# run the actual benchmark
start = time.time()
for i in xrange(10000):
    s = banana.encode([i, i*2, "hello", "there"])
    banana.decode(s)

elapsed = time.time() - start
print elapsed, "seconds (%s messages a second)" % (10000 / elapsed)
