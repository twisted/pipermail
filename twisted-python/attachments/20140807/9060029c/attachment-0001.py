from twisted.spread import pb
from example import CopyDictionary, RemoteDictionary
from twisted.internet import reactor
from twisted.internet import defer

factory = pb.PBClientFactory()
reactor.connectTCP("localhost", 7999, factory)
        
pb.setUnjellyableForClass(CopyDictionary, RemoteDictionary)

def use_dictionary(dictionary):
    for w in dictionary.words.keys():
	for d in dictionary.words[w]:
	    print w, d
    reactor.callLater(10, use_dictionary, dictionary)

def goto_library():
    return factory.getRootObject()

import sys
language = 'english'
if len(sys.argv) > 1:
    language = sys.argv[1]

def test():
    d = goto_library()
    d.addCallback(lambda root: root.callRemote('dictionary', language))
    d.addCallback(use_dictionary)
    return d

reactor.callWhenRunning(test)
reactor.run()

