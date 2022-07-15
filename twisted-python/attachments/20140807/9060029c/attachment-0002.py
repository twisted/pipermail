from twisted.spread import pb
from twisted.internet import reactor
from twisted.internet import defer

factory = pb.PBClientFactory()
reactor.connectTCP("localhost", 7999, factory)

def goto_library():
    return factory.getRootObject()

def define_result(ans, language, word, definition):
    # audit submission later
    print ans
    reactor.stop()
import sys 
language = 'english'
if len(sys.argv) > 1:
    language = sys.argv[1]
word = language
if len(sys.argv) > 2:
    word = sys.argv[2]
definition = word + ' is part of ' + language
if len(sys.argv) > 3:
    definition = sys.argv[3]

print 'language', language
print 'word', word
print 'definition', definition

def test():
    d = goto_library()
    d.addCallback(lambda root: root.callRemote('define', language, word, definition))
    d.addCallback(define_result, language, word, definition)
    return d

reactor.callWhenRunning(test)
reactor.run()

