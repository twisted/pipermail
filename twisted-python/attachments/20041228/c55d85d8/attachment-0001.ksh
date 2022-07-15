from twisted.spread import pb

class MyError(pb.Copyable, pb.Error, pb.RemoteCopy):
    def __init__(self, msg):
        pb.Error.__init__(self)
        self.msg = msg
    def getMsg(self):
        return self.msg

pb.setUnjellyableForClass(MyError, MyError)
