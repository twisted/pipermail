
from compstrm.twcs import pollLoop, _patchCallLater, CompStrm
from compstrm import pipe
import time

class WriteMany(CompStrm):
    def cs(self):
        for i in range(self.lmt):
            self.device[1].startWrite(i)
            yield False
            self.device[1].endWrite()

class ReadCount(CompStrm):
    def cs(self):
        c=0
        while True:
            self.device[0].startRead()
            yield False
            try:
                data=self.device[0].endRead()
                c+=1
            except pipe.PipeEofException:
                break
        print c

def test():
    p=pipe.Pipe()

    write=WriteMany()
    pipe.setIO(write,None,p)
    write.lmt=100000
    write.run()

    reader=ReadCount()
    pipe.setIO(reader,p)
    reader.run()

    t0=time.time()
    pollLoop()
    t1=time.time()
    print (t1-t0)/write.lmt
    print write.lmt/(t1-t0),'per second'

print "Pristine Twisted"
test()
print "callLater-Patched Twisted"
_patchCallLater()
test()
