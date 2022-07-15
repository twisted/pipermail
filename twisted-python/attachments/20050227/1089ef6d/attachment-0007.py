# $Source: /repo/step_testbed/PanGalactic/pangalactic/utils/xmlrpcinterface.py,v $

"""
PanGalactic Client XML-RPC Interfaces

@version: $Revision: 1.75 $
"""

__version__ = "$Revision: 1.75 $"[11:-2]

import base64
import xmlrpclib
import string
import httplib
from pangalactic.meta.factory import PanGalacticFactory


class BasicAuthTransport(xmlrpclib.Transport):
    """
    Transport for basic authenticated XML-RPC channel.
    (Thanks to Amos's Zope Page for this code. :)
    """

    def __init__(self, username=None, password=None):
        self.username=username
        self.password=password
        self.verbose = 0

    def request(self, host, handler, request_body, verbose=0):
        # issue XML-RPC request

        h = httplib.HTTP(host)
        h.putrequest("POST", handler)

        # required by HTTP/1.1
        h.putheader("Host", host)

        # required by XML-RPC
        h.putheader("User-Agent", self.user_agent)
        h.putheader("Content-Type", "text/xml")
        h.putheader("Content-Length", str(len(request_body)))

        # basic auth
        if self.username is not None and self.password is not None:
            h.putheader("AUTHORIZATION", "Basic %s" % string.replace(
                base64.encodestring("%s:%s" % (self.username, self.password)),
                "\012", ""))
        h.endheaders()

        if request_body:
            h.send(request_body)

        errcode, errmsg, headers = h.getreply()

        if errcode != 200:
            raise xmlrpclib.ProtocolError(
                host + handler,
                errcode, errmsg,
                headers
                )

        return self.parse_response(h.getfile())


class SafeBasicAuthTransport(xmlrpclib.SafeTransport):
    """
    Transport for basic authenticated XML-RPC channel.
    (Thanks to Amos's Zope Page for this code. :)
    """

    def __init__(self, username=None, password=None):
        self.username=username
        self.password=password
        self.verbose = 0

    def request(self, host, handler, request_body, verbose=0):
        # issue XML-RPC request

        h = httplib.HTTPS(host)
        h.putrequest("POST", handler)

        # required by HTTP/1.1
        h.putheader("Host", host)

        # required by XML-RPC
        h.putheader("User-Agent", self.user_agent)
        h.putheader("Content-Type", "text/xml")
        h.putheader("Content-Length", str(len(request_body)))

        # basic auth
        if self.username is not None and self.password is not None:
            h.putheader("AUTHORIZATION", "Basic %s" % string.replace(
                base64.encodestring("%s:%s" % (self.username, self.password)),
                "\012", ""))
        h.endheaders()

        if request_body:
            h.send(request_body)

        errcode, errmsg, headers = h.getreply()

        if errcode != 200:
            raise xmlrpclib.ProtocolError(
                host + handler,
                errcode, errmsg,
                headers
                )

        return self.parse_response(h.getfile())


class XmlrpcInterface:
    """
    XML-RPC API to PGER
    """

    def __init__(self, host, port, username='', password='',
                 secure=1, domains='PanGalactic', _registry=None): 
        # proxyhost=None, proxyport=None ...
        # (we'll worry about proxies later :)
        self._factory = PanGalacticFactory(_registry=_registry,
                                           domains=domains)
        if secure:
            # not tested, according to xmlrpclib docs
            conns = 'https://'
        else:
            conns = 'http://'
        conns = conns + host + ':' + str(port)
        print 'XmlrpcInterface:  connection string is', conns
        if username and password:
            self.username = username
            if secure:
                self._RPC =  xmlrpclib.ServerProxy \
                                (conns,
                                 SafeBasicAuthTransport(username,
                                                        password))
            else:
                self._RPC =  xmlrpclib.ServerProxy(conns,
                                 BasicAuthTransport(username,
                                 password))
        else:
            self._RPC =  xmlrpclib.ServerProxy(conns)

        self.not_yet_list = ["PartsList",
                             "GidepAgencyActionNotice",
                             "GidepProductChangeNotice",
                             "GidepDmsmsNotice"]
#                             "GidepAlert",
#                             "GidepProblemAdvisory",
#                             "NasaAdvisory",
#                             "ProblemImpactStatement"]
    

    def yo(self):
        return self._RPC.yo()

    def openPodBayDoor(self):
        return self._RPC.openPodBayDoor()
    
    def changePassword(self, password, username=''):
        if not username:
            username = self.username
        elif username != self.username and username != 'admin':
            raise ValueError, "Only admin can change others' passwords."
        return self._RPC.changePassword(password, username)

    def addObjects(self, object_list, objlist = None):
        #print "xmlrpc.addobjects"
        if not objlist:
            objlist = []
        newobjects = []
        if object_list:
            #print "object_list", object_list
            #for o in object_list:
            #    print "fileobj", o
            if type(object_list) is list:
                # deporder = self._factory.getDependencyOrder()
                extracts = [self._factory.extract(o) for o in object_list]
                newexts = self._RPC.addObjects(extracts)
                newobjects, object_list = self._factory.rememberAll(newexts, objlist)
            else:
                extracts = [self._factory.extract(o)]
                newexts = self._RPC.addObjects(extracts)
                newobjects, object_list = self._factory.rememberAll(newexts)
        return newobjects
                
        

    def getObjects(self, classname, fields, refs=0, subtypes=0,
                   objs=None, is_head=True):
        """
        Retrieve the objects that have the field-value pairs in fieldvaluedict.
        
        @type classname:  string
        @param classname: class name of desired objects

        @type fields:  dictionary
        @param fields: search criteria as attribute:value pairs

        @type refs:  integer (0 or 1)
        @param refs: flag for whether or not referenced object
                     are also retrieved.

        @type subtypes:  integer (0 or 1)
        @param subtypes: flag for whether or not subclasses of
                         classname are also retrieved.

        @type objs:  list 
        @param objs: objects to be hooked up.  Don't worry if you
                     pass an irrelevent object.
        """
        #print "xmlrpc.getobjects"
        # get only the latest version for versioned objects, if requested
        if is_head:
            if classname in ["Part", "Document", "Model",
                             "PgefObjectSchema", "PartsList"]:
                fields["is_head"] = True

        if objs == None:
            objs = []

        data = self._RPC.getObjects(classname, refs, subtypes, fields)
        if data:
            newobjs, objs = self._factory.rememberAll(data, objs)
            return newobjs
        #else:
        #    print "no data"


    def getCategories(self, context):
        """
        Get all Category objects for the given context.
        """
        crit = {"id_ns" : context}
        data = self._RPC.getObjects("PgefObjectSchema", 0, 0, crit)
        if data:
            newobjs, objs = self._factory.rememberAll(data, [])
            return newobjs


    def getOrganizations(self, context):
#        print "xmlrpc.getorganizations", context
        crit = {"id_ns" : context}
        data = self._RPC.getObjects('Organization', 0, 0, crit)
        if data:
            newobjs, objs = self._factory.rememberAll(data, [])
            return newobjs


    def getLinkedObjs(self, classname, criteria, objs = None):
        #print "xmlrpcinterface.getlinkedobjs"
        if objs == None:
            objs = []
        data = self._RPC.getObjects(classname, 1, 0, criteria)
        if data:
            newobjs, objs = self._factory.rememberAll(data, objs)
            return newobjs


    def approveUser(self, user_info):
        print "xmlrpc.approveuser"

    def requestUser(self, user_info):
        print "xmlrpc.requestuser"

        
    def search(self, class_attr_dict, localobjs = None):
        """
        Return a list of objects in any of the classes in class_attr_dict
        that satisfy the (attr, attrvalue) pairs.
        
        @type class_attr_dict: dictionary
        @param class_attr_dict: looks like
            {classname:(attrname, comparator, attrvalue), ...}
        """
        print "xmlrpcinterface.search", class_attr_dict
        if localobjs == None:
            localobjs = []
        retlist = []
        for classname, attrlist in class_attr_dict.items():
            #print "searching for", classname
            if classname in self.not_yet_list:
                #print "Search for", classname, "is TBD RSN"
                continue
            objlist = []
            #print "  ", classname, attrlist
            # do not get back referenced objects for now (first 0/1)
            # do get back subtypes (second 0/1)
            if len(attrlist) == 0:
                continue
            data = self._RPC.search(classname, 0, 1, attrlist)
            if data:
                #print "  #data found", len(data)
                #for d in data:
                #    print d["id"], d["description"]
                objlist, localobjs = self._factory.rememberAll(data, localobjs)
                #print "len objlist", len(objlist)
                #print "len localobjs", len(localobjs)
                for obj in objlist:
                    if obj.__class__.__name__ == classname:
                        retlist.append(obj)
            else:
                print "no data found for", classname
        return retlist        
    
        
        
    def searchAlerts(self, class_attr_dict, localobjs = None):
        """
        Return a list of objects in any of the classes in class_attr_dict
        that satisfy the (attr, attrvalue) pairs.
        
        @type class_attr_dict: dictionary
        @param class_attr_dict: looks like {classname:(attrname, attrvalue, comparator),}
        """
        #print "xmlrpcinterface.searchAlerts", class_attr_dict
        if localobjs == None:
            localobjs = []
        retlist = []
        for classname, attrlist in class_attr_dict.items():
            #print "searching for", classname
            if classname in self.not_yet_list:
                print "Search for", classname, "is TBD RSN"
            if len(attrlist) == 0:
                continue

            objlist = []
            # do not get back referenced objects for now (first 0/1)
            # do get back subtypes (second 0/1)
            data = self._RPC.search(classname, 0, 1, attrlist)
            if data:
                #print "  #data found", len(data)
                #for d in data:
                #    print d["id"], d["description"]

                objlist, localobjs = self._factory.rememberAll(data, localobjs)
                for obj in objlist:
                    if obj.__class__.__name__ == classname:
                        retlist.append(obj)
            else:
                print "no data found", classname
        return retlist        
    
 
    def startWfActivity(self, wf_activity, wf_obj):
        print "xmlrpc.startActivity", wf_activity.name, wf_obj.name
       


