"""
PGER XML-RPC Interfaces module
@version: $Revision: 1.17 $
"""

__version__ = "$Revision: 1.17 $"[11:-2]
# $Id: pgerxmlrpc.py,v 1.17 2005/01/29 21:52:47 waterbug Exp $

from twisted.python import log
from twisted.web.xmlrpc import XMLRPC
from twisted.web import resource
from twisted.internet.defer import succeed, fail
from pangalactic.utils.datetimes import isoToDateTime
from pangalactic.utils.pgefexceptions import *


class PgerXmlrpcService(XMLRPC):
    """
    I am a Web resource that publishes PGEF Node services
    via XML-RPC.  In my initial implementation, I provide an
    interface to a Node configured with a PGER Service.
    """

    __implements__ = resource.IResource

    def __init__(self, engine=None, userid=None):
        XMLRPC.__init__(self)
        self.engine = engine
        self.userid = userid

    def _getFunction(self, functionPath):
        """
        Extends XMLRPC._getFunction to include a log entry
        """
        s = '%s:PgerXmlrpcService' % self.userid
        log.msg(functionPath, system=s)
        return XMLRPC._getFunction(self, functionPath)

    def logout():
        pass

    def xmlrpc_yo(self):
        """
        XMLRPC yo.
        """
        return 'Yo'

    def xmlrpc_openPodBayDoor(self):
        """
        XMLRPC request to open the Pod Bay Door.
        """
        return """I'm sorry, Dave, I'm afraid I can't do that."""

    def xmlrpc_echoargs(self, *args):
        """
        XMLRPC request for echo of arguments.
        """
        if args:
            return args
        else:
            s = """Nothin' from nothin' LEAVES nothin', """
            s += """ya gotta have somethin' ...!"""
            return s

    def xmlrpc_echobinary(self, blob):
        """
        XMLRPC request with binary data.
        """
        if blob:
            comment = 'I got this from you'
            return [comment, blob]
        else:
            s = """Nothin' from nothin' LEAVES nothin', """
            s += """ya gotta have somethin' ...!"""
            return s

    
    def xmlrpc_changePassword(self, password, userid=''):
        """
        Change password for a userid (default: for
        the authenticated user).

        @type password:   string
        @param password:  new password

        @type userid:   string
        @param userid:  pgef_oid of the Person whose password is to be
            changed
        """
        return self.engine.changePassword(self.userid,
                                          userid,
                                          password)

    def xmlrpc_getObjects(self, typename, refs, subtypes, criteria):
        """
        XMLRPC getObjects:  get the set of objects that exactly match a
        specified set of attribute-value pairs, returning the result as a
        list of "extracts" -- see L{pangalactic.utils.factory.extract})

        @type typename:   string
        @param typename:  the name of a class that extends
                          L{pangalactic.core.pgefobject.PgefObject}

        @type refs:   boolean
        @param refs:  whether to return all referenced objects or
                      only the specified class
                          0:  (default) only the specified class
                          1:  include all reference objects

        @type subtypes:   boolean
        @param subtypes:  whether to return all subtypes of the
                          requested type that match the criteria
                              0:  (default) not
                              1:  include all subtypes

        @type criteria:   list or dictionary
        @param criteria:  the selection criteria can take either
                          of two forms:
                              - list:  a list of [attr, value] pairs
                              - dict:  a dictionary: {attr : value, ...}
        """
        if criteria:
            if isinstance(criteria, list):
                kw = dict(criteria)
            elif isinstance(criteria, dict):
                kw = criteria
            res = self.engine.getObjects(requestor=self.userid,
                                         schemaid=typename,
                                         refs=refs,
                                         subtypes=subtypes,
                                         **kw)
            return res
        else:
            return """I'm sorry, Dave, I'm afraid I can't do that."""

    def xmlrpc_search(self, schemaid, refs, subtypes, args):
        """
        Search for instances of the specified class.

        @type schemaid:   string
        @param schemaid:  the id of the class of objects to search for
            (i.e., a subtype of
            L{pangalactic.core.pgefobject.PgefObject})

        @type  refs:  boolean
        @param refs:  specifies whether to include objects
                    referenced by the found objects (i.e.,
                    the attributes whose types are classes in the
                    ontology).
                        0:  (default) do not get refs
                        1:  get all references
                    (in future, refs may specify how many
                    reference levels to follow ...)

        @type  subtypes:  boolean
        @param subtypes:  specifies whether to include only the
                    specified class (the default) or all
                    subtypes.
                        0:  (default) only this type
                        1:  include subtypes

        @type  objects:  boolean
        @param objects:  specifies whether to return objects
                    of the type specified or resultsets.
                        0:  resultsets
                        1:  objects

        @type args:   sequence
        @param args:  a list of query element tuples, in which each
                    tuple has the form:
                        - element[0] = attribute name
                        - element[1] = logical operator
                        - element[2] = search value
                    ... where operator can be any SQL operator,
                    e.g.: 'LIKE', '=', '<', '>', etc.  Note that
                    if the operator is 'LIKE' and the attribute
                    is a string, a case-independent search will
                    be done, treating the search value as a
                    substring.
        """
        return self.engine.findObjects(self.userid, schemaid, refs, subtypes,
                                       args=args)

#     def xmlrpc_getDocuments(self, typename, refs,
#                             subtypes, criteria):
#         """
#         XMLRPC getDocuments:  get the set of Documents that exactly
#         match a specified set of attribute-value pairs, returning
#         the result as a list of "extracts" -- see
#         L{pangalactic.utils.factory.extract})
# 
#         @type typename:   string
#         @param typename:  the name of a class that extends
#                           L{pangalactic.core.document.Document}
# 
#         @type refs:   boolean
#         @param refs:  whether to return all referenced objects or
#                       only the specified class
#                           0:  (default) only the specified class
#                           1:  include all reference objects
# 
#         @type subtypes:   boolean
#         @param subtypes:  whether to return all subtypes of the
#                           requested type that match the
#                           criteria
#                               0:  (default) not
#                               1:  include all subtypes
# 
#         @type criteria:   list or dictionary
#         @param criteria:  the selection criteria can take either
#                           of two forms:
#                               - list:  a list of [attr, value] pairs
#                               - dict:  a dictionary: {attr : value, ...}
#         """
#         if criteria:
#             if isinstance(criteria, list):
#                 kw = dict(criteria)
#             elif isinstance(criteria, dict):
#                 kw = criteria
#             res = self.engine.getDocuments(typename, refs,
#                                          subtypes, **kw)
#             res.addCallback(self.engine._factory.docrsl2Extract)
#             return res
#         else:
#             return """I'm sorry, Dave, I'm afraid I can't do that."""

    def xmlrpc_addObjects(self, extracts):
        """xmlrpc method to add objects.

        @type extracts:   list
        @param extracts:  a list of extracts (for the definition
                          of extracts, see
                          L{pangalactic.utils.factory.PgefFactory})

        @rtype:   list
        @return:  a list of extracts:  the objects that were
                  added, with any relevant updates (e.g.,
                  timedate stamps)
        """
        if extracts:
            return self.engine.addObjects(self.userid, extracts)
        else:
            return """I'm sorry, Dave, I'm afraid I can't do that."""

    def xmlrpc_addObjectsAndBlobs(self, extracts, blobs):
        """
        XML-RPC method to add objects.

        @type extracts:   list
        @param extracts:  a list of extracts (for the definition
                          of extracts, see
                          L{pangalactic.utils.factory.PgefFactory})

        @type blobs:  list
        @param blobs: a list of binary objects, which will be
                      saved to files on the server and referenced
                      from PgefFile objects.  NOTE:  for each blob,
                      there should be a corresponding
                      L{pangalactic.core.pgeffile.PgefFile}
                      instance in the list of extracts, and they
                      should occur in the same order in the
                      extracts as their blob occurs in the blobs
                      list.

        @rtype:   list
        @return:  a list of extracts:  the objects that were
                  added, with any relevant updates (e.g.,
                  timedate stamps)
        """
        if extracts and data:
            try:
                res = self.engine.addExtracts(self.userid,
                                              extracts)
            except:
                text = """I'm sorry, Dave, there was a problem"""
                text += """with your objects."""
                return text
            # if the extracts have been added successfully, write
            # the blobs to files ...
        elif extracts:
            return self.engine.addExtracts(self.userid, extracts)
        else:
            return """I'm sorry, Dave, I'm afraid I can't do that."""





