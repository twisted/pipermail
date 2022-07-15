# -*- test-case-name: twisted.test.test_xdbapi -*-
# Twisted, the Framework of Your Internet
# Copyright (C) 2003 Matthew W. Lefkowitz
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of version 2.1 of the GNU Lesser General Public
# License as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""
Long lived database transactions.
"""

from twisted.spread import pb
from twisted.internet import defer
from twisted.internet import threads, reactor
from twisted.python import reflect, log, failure


class ConnectionPool(pb.Referenceable):
    """I represent a pool of connections to a DB-API 2.0 compliant database.

    The minimum number of connections is hardcoded to 3, the maximum to 5, but
    this can be changed by subclassing and changing the connmax and connmin
    class variables and/or calling setConnectionLimits() at runtime.
    """
    connmax = 5
    connmin = 3
    
    def __init__(self, dbapiName, *args, **kwargs):
        """Initialize the connection pool.

        This method will initialize:
        
            1) the connection to the database using the DBAPI
            2) the number of minimum and maximum available connections,
               by pre-opening a number of connections equal to minconn.
            3) the shutdown method
        """
        self.dbapiName = dbapiName
        self.connargs = args
        self.connkwargs = kwargs
        
        self.dbapi = reflect.namedModule(dbapiName)
        assert self.dbapi.apilevel == '2.0', \
               'DB API module not DB API 2.0 compliant.'
        assert self.dbapi.threadsafety > 0, \
               'DB API module not sufficiently thread-safe.'

        if kwargs.has_key('connmin'):
            self.connmin = kwargs['connmin']
            del kwargs['connmin']
        else:
            self.connmin = self.connmin
        if kwargs.has_key('connmax'):
            self.connmax = kwargs['connmax']
            del kwargs['connmax']
        else:
            self.connmax = self.connmax
        
        self._connections = []
        self._transactions = []    

        self.shutdownID = reactor.addSystemEventTrigger(
            'during', 'shutdown', self.finalClose)

    def __getstate__(self):
        """Save the state."""
        return {'dbapiName': self.dbapiName,
                'connmin': self.connmin,
                'connmax': self.connmax,
                'connargs': self.connargs,
                'connkwargs': self.connkwargs,}

    def __setstate__(self, state):
        """Restore the state.

        Note that everything is restored, even the number of connections.
        """
        self.__dict__ = state
        apply(self.__init__, (self.dbapiName,)+self.connargs, self.connkwargs)
        self.setConnectionLimits(state['connmin'], state['connmax'])

    def setConnectionLimits(self, connmin, connmax):
        """Sets the minimum and maximum number of connections."""
        self.connmin = connmin
        self.connmax = connmax
        
    def _connect(self):
        """Try to get a connection from the pool."""
        try:
            return self._connections.pop()
        except IndexError:
            pass
        
        # can we allocate a new connection?
        if len(self._connections) + len(self._transactions) < self.connmax:
            conn = apply(self.dbapi.connect, self.connargs, self.connkwargs)

            log.msg('xdbapi connecting: %s %s %s' % (
                self.dbapiName, self.connargs or '', self.connkwargs or ''))
            return conn

        # no, we exceded the limit, raise an error
        else:
            raise IndexError("maximum number of connections reached")

    def _release(self, conn):
        """Release a connection to the pool.

        Note that a connection is destroyed only if it is in excess of
        self.connmin, else it is retained in the pool.
        """
        if len(self._connections) > self.connmin:
            print "destroying connection", self.connmin
            log.msg('xdbapi closing: %s %s %s' %
                (self.dbapiName, self.connargs or '', self.connkwargs or ''))
            conn.close()
        else:
            self._connections.append(conn)

    def _begin(self):
        """Allocate and return a new transaction.

        This method will possibly open a new connection to the database and
        should be called as a separate thread (it will block.)
        """
        conn = self._connect()
        trans = Transaction(self, conn)
        self._transactions.append(trans)
        return trans

    def _commit(self, trans):
        """Commit given transaction.

        The transaction is committed and then the connection is returned to
        the connection pool.
        """
        conn = trans._commit()
        self._release(conn)
        self._transactions.remove(trans)
        
    def _rollback(self, trans, conn=None):
        """Rollback given transaction.

        The transaction is rolled back and then the connection is returned to
        the connection pool.
        """
        if conn is None:
            conn = trans._rollback()
        self._release(conn)
        self._transactions.remove(trans)
        
    def begin(self):
        """Start a new transaction."""
        return threads.deferToThread(self._begin)

    def commit(self, trans):
        """Start a new transaction."""
        return threads.deferToThread(self._commit, trans)

    def rollback(self, trans):
        """Start a new transaction."""
        return threads.deferToThread(self._rollback, trans)

    def close(self):
        """Shut down the connection pool."""
        if self.shutdownID:
            reactor.removeSystemEventTrigger(self.shutdownID)
            self.shutdownID = None
        self.finalClose()

    def flush(self):
        """Reset (rollback) all the active transactions."""
        for trans in self._transactions[:]:
            self.rollback(trans)
            
    def finalClose(self):
        """Really close all the transactions and connections.

        TODO: we had notification here; what about adding a callback?
        """
        self.flush()
        for conn in self._connections:
            log.msg('xdbapi closing: %s %s %s' %
                (self.dbapiName, self.connargs or '', self.connkwargs or ''))
            self._connections.remove(conn)
            conn.close()

    ## some utility functions ##

    def runOperation(self, *args, **kwargs):
        """Create a new transaction and run the given operation."""
        return threads.deferToThread(
            self._runCallback, '_runOperation', *args, **kwargs)

    def runQuery(self, *args, **kwargs):
        """Create a new transaction and run the given operation."""
        return threads.deferToThread(
            self._runCallback, '_runQuery', *args, **kwargs)

    def _runCallback(self, method, *args, **kwargs):
        """Run he database operation."""
        trans = self._begin()
        func = getattr(trans, method)
        try:
            result = func(*args, **kwargs)
            self._commit(trans)
            return result
        except StandardError, err:
            # connection has already been rolled back
            raise err


class Transaction:
    """This is a single database transaction."""

    def __init__(self, pool, connection):
        """Initialize this transaction with given connection."""
        self._connection = connection
        self._pool = pool
        self._cursor = connection.cursor()
        # now initialize the cursor wrapper methods
        self.execute =  self._cursor.execute
        self.executemany =  self._cursor.executemany
        self.fetchone =  self._cursor.fetchone
        self.fetchmany =  self._cursor.fetchmany
        self.fetchall =  self._cursor.fetchall

    def commit(self):
        """A wrapper method that commit and remove from the pool."""
        return self._pool.commit(self)

    def rollback(self):
        """A wrapper method that roll back and remove from the pool."""
        return self._pool.rollback(self)

    def runOperation(self, *args, **kwargs):
        """Run an asynchronous database operation."""
        return threads.deferToThread(self._runOperation, *args, **kwargs)

    def runQuery(self, *args, **kwargs):
        """Run an asynchronous database query."""
        return threads.deferToThread(self._runQuery, *args, **kwargs)
    
    def _commit(self):
        """Close the cursor (making it unavailable) and commit."""
        self._cursor.close()
        self._connection.commit()
        return self._connection
    
    def _rollback(self):
        """Close the cursor (making it unavailable) and rollback."""
        self._cursor.close()
        self._connection.rollback()
        return self._connection

    def _runOperation(self, *args, **kwargs):
        """Map the operation to an execute call."""
        try:
            self.execute(*args, **kwargs)
        except StandardError, err:
            log.msg('xdbapi error during execute:\n    ' + str(err))
            log.deferr()
            self._pool._rollback(self)
            raise err
        
    def _runQuery(self, *args, **kwargs):
        """Map the query to an execute call."""
        self._runOperation(*args, **kwargs)
        return self.fetchall()
