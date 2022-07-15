from twisted.python import roots, components
import string
import dircache

ftp_reply = {
    'welcome': ['Welcome to Twisted FTP','','This is a multiline reply']
    }

def printFTPReply(code, slist):
    """Converts a code + a list of strings into an FTP-style reply"""
    a = []
    for b in xrange(len(slist[:-1])):
        a.append(str(code)+'-'+slist[b])
    a.append(str(code)+' '+slist[-1:][0])
    return a

def parseFTPReply(slist):
    """Converts a list of FTP-style-reply strings into a (code, list of strings)"""
    code = int(slist[0][:3])
    a = []
    for b in slist:
        a.append(b[4:])
    return (code, a)

class IPropertyManager(components.Interface):
    """A manager of properties

    def getPropertyDate():
        return date
    """

class PropertyManager(components.Interface):
    __implements__ = IPropertyManager
    readproperties = [] # A list of properties
    writeproperties = [] # A list of properties

    def getProperty(self, key):
        if key in self.readproperties:
            method = getattr(self, "getProperty%s" % key, None)
            return method()
        else:
            raise KeyError("Property does not exist (%s)" % key)

    def setProperty(self, key, value):
        if key in self.writeproperties:
            method = getattr(self, "setProperty%s" % key, value)
            return method
        else:
            if key in self.readproperties:
                raise roots.ConstraintViolation("Property is read only (%s)" % key)
            else:
                raise KeyError("Property does not exist (%s)" % key)

    def getPropertyNames(self):
        return self.readproperties # Simple

    def getProperties(self, propertylist):
        d = {}
        for key in propertylist:
            d[key] = self.getProperty(key)
        return d

    def getAllProperties(self):
        return self.getProperties(self.readproperties)

class IEntity(components.Interface):
    """A entity"""

class ICollection(components.Interface):
    """A resource"""

class Path:
    """State machine for paths, use with care

    Since I wrote this, I discovered posixpath which is what I was looking for. 
    Outputs (and internally) list of strings"""
    path = []
    rootpath = ''

    def __init__(self, rootpath, path):
        self.rootpath = rootpath
        self.cwd(path)

    def cwdlist(self, relativepaths):
        """Change WorkingDirectory
        Changes self.path according to the list relativepaths, safely"""
        for relativepath in relativepaths:
            if len(relativepath)==0:
                raise roots.ConstraintViolation("Tried to access nothing") # catches '//' as well
            if (relativepath=='/'):
                self.path=[]
                return
            if string.find(relativepath, '/') is not -1:
                raise roots.ConstraintViolation("Strange: a '/' in a filename") # catches '//' as well
            if (relativepath=='.'):
                return 
            if (relativepath=='..'):
                self.cwdup()
                return
            self.path.append(relativepath)        
            return

    def joinPath(self, path, relativepath):
        tmppath = path[:]
        if len(relativepath)==0:
            raise roots.ConstraintViolation("Tried to access nothing") # catches '//' as well
        if (relativepath=='/'):
            tmppath=[]
            return tmppath
        if string.find(relativepath, '/') is not -1:
            pathlist = string.split(relativepath,'/')
            for relativepath in pathlist:
                if relativepath == '':
                    relativepath = '/'
                tmppath = self.cwd(relativepath) # one level recursion
            return      
        if (relativepath=='.'):
            return tmppath
        if (relativepath=='..'):
            if len(tmppath) > 1:
                return tmppath[:-1]
        tmppath.append(relativepath)        
        return tmppath

    
    def cwd(self, relativepath):
        """Change WorkingDirectory
        Changes self.path according to the string relativepath, safely"""
        self.path = self.joinPath(self.path, relativepath)

    def cwdup(self):
        if len(self.path) > 1:
            self.path = self.path[:-1]
        return
    
    def __repr__(self):
        return '/'+string.join(self.path,'/')

    def buildPath(self):
        return self.rootpath + self.__repr__()

class Request(roots.Request):
    wireProtocol = 'FTP'
    startedWriting = 0
    path = []
    def write(self, data):
        raise NotImplementedError, "No idea what I should write"

    def finish(self):
        raise NotImplementedError, "No idea where to return stuff"

class CommonProperties(PropertyManager):
    __implements__ = [IPropertyManager]
    PropertyManager.readproperties.extend(["ModifiedTime"])

    def getPropertyModifiedTime(self):
        path = self.path.buildPath()
        return os.path.getmtime(path)

class DirectoryProperties(CommonProperties):
    __implements__ = [IPropertyManager]
    PropertyManager.readproperties.extend([])

class FileProperties(CommonProperties):
    __implements__ = [IPropertyManager]

    PropertyManager.readproperties.extend(["Size"])

    def getPropertySize(self):
        path = self.path.buildPath()
        return os.path.getsize(path)

class File(roots.Entity, FileProperties):
    __implements__ = IEntity, IPropertyManager
    dir = None
    path = None
    rootpath = None

    def __init__(self, rootpath, initpath):
        self.path = Path(rootpath, '/')
        self.path.cwd(initpath)
        self.rootpath = rootpath

    def render(self, request):
        "This is not a proper name for an FTP read"
        pass        

    def open(self, mode="r"):
        "Simple fileacces method"
        return open(self.path.buildPath(), mode)
        
class Directory(roots.Collection, DirectoryProperties):
    __implemenents__ = ICollection, IPropertyManager
    dir = None
    path = None
    rootpath = None

    def entityImplements(self, rootpath, initpath):
        path = Path(rootpath, '/')
        path.cwd(initpath)
        p = path.buildPath()
        if os.path.isdir(p):
            return ICollection
        if os.path.isfile(p):
            return IEntity

    def __init__(self, rootpath, initpath):
        self.path = Path(rootpath, '/')
        self.path.cwd(initpath)
        self.rootpath = rootpath
        
    def listDynamicEntities(self):
        di = dircache.listdir(self.path.buildPath())
        l = {}
        for a in di:
            path = self.path.path
            request = Request() # FIXME: Ugly
            request.path = self.path.joinPath(path, a)[0]
            l[a] = self.getDynamicEntity(request)
        return l.items()

    def listDynamicNames(self):
        di = dircache.listdir(self.path.buildPath())
        return di[:]

    def getDynamicEntity(self, request):
        i = self.entityImplements(self.rootpath, request.path)
        if i == ICollection: 
            return Directory(self.rootpath, request.path)
        if i == IEntity:
            return File(self.rootpath, request.path)

class FileSystem(Directory):
    "Hm"

a = FileSystem('c:/','/')
r = Request()
r.path = 'Python21\PIL.PTH'
b = a.getDynamicEntity(r)
print r.path, b.getProperty("Size")
l= a.listDynamicEntities()
for c in l:
    f, g = c
    print f, time.ctime(g.getProperty("ModifiedTime"))
