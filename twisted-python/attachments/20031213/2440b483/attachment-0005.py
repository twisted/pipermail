# Twisted, the Framework of Your Internet
# Copyright (C) 2001-2002 Matthew W. Lefkowitz
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
# 

"""Tests for twisted.enterprise.xdbapi"""

from twisted.trial import unittest

try:
    from twisted.enterprise.xdbapi import ConnectionPool
except:
    from xdbapi import ConnectionPool
from twisted.trial.util import deferredResult, deferredError
from twisted.python import log

try: from pyPgSQL import PgSQL
except: PgSQL = None

try: import MySQLdb
except: MySQLdb = None

try: import psycopg
except: psycopg = None

simple_table_schema = """
CREATE TABLE simple (
  x integer
)
"""

class XDBAPITestCase:
    """Base class for testing xdbapi."""

    count = 100
    can_rollback = 1
    can_isolate = 1
    
    DB_NAME = 'test'
    DB_USER = 'fog'
    DB_PASS = 'twisted_test'
    
    def setUp(self):
        self.createPool()

    def tearDown(self):
        self.destroyPool()

    def createPool(self):
        self.startDB()
        self.dbpool = self.makePool()
        deferredResult(self.dbpool.runOperation(simple_table_schema))

    def destroyPool(self):
        self.dbpool.flush()
        deferredResult(self.dbpool.runOperation('DROP TABLE simple'))
        self.dbpool.close()
        self.stopDB()

    def checkConnections(self, expected):
        n = len(self.dbpool._connections)
        err = "Wrong number of connections in pool (e: %d, f: %d)."
        self.failUnless(n == expected, err % (expected, n))

    def checkTransactions(self, expected):
        n = len(self.dbpool._transactions)
        err = "Wrong number of open transactions (e: %d, f: %d)."
        self.failUnless(n == expected, err % (expected, n))
        
    def testPool(self):
        # let's start the check by veryfing the pool works the right way
        trans = deferredResult(self.dbpool.begin())
        self.checkConnections(0)
        self.checkTransactions(1)

        unusedtrans = deferredResult(self.dbpool.begin())
        self.checkConnections(0)
        self.checkTransactions(2)

        # let's have the start method fail by using all the connections
        deferredError(self.dbpool.begin())
        log.flushErrors()
        self.checkConnections(0)
        self.checkTransactions(2)

        # now we give trans a wrong query, we expect it to rollback and remove
        # itself from the pool
        deferredError(trans.runOperation("XXX"))
        log.flushErrors()
        self.checkConnections(1)
        self.checkTransactions(1)

        # commit on the other connection, does nothing
        deferredResult(unusedtrans.commit())
        self.checkConnections(2)
        self.checkTransactions(0)

        # and finally reallocate two transactions
        trans = deferredResult(self.dbpool.begin())
        unusedtrans = deferredResult(self.dbpool.begin())
        self.checkConnections(0)
        self.checkTransactions(2)

        deferredResult(trans.rollback())
        deferredResult(unusedtrans.commit())
        self.checkConnections(2)
        self.checkTransactions(0)
        
    def testSQL(self):
        # make sure failures are raised correctly
        deferredError(self.dbpool.runQuery("select * from NOTABLE"))
        deferredError(self.dbpool.runOperation("delete from * from NOTABLE"))
        log.flushErrors()

        self.checkConnections(1)
        self.checkTransactions(0)

        # verify simple table is empty
        sql = "select count(1) from simple"
        row = deferredResult(self.dbpool.runQuery(sql))
        self.failUnless(int(row[0][0]) == 0, "Interaction not rolled back")

        # add some rows to simple table (runOperation)
        for i in range(self.count):
            sql = "insert into simple(x) values(%d)" % i
            deferredResult(self.dbpool.runOperation(sql))

        # make sure they were added (runQuery)
        sql = "select x from simple order by x";
        rows = deferredResult(self.dbpool.runQuery(sql))
        self.failUnless(len(rows) == self.count, "Wrong number of rows")
        for i in range(self.count):
            self.failUnless(len(rows[i]) == 1, "Wrong size row")
            self.failUnless(rows[i][0] == i, "Values not returned.")

        # now let's do the same using a single transaction
        trans = deferredResult(self.dbpool.begin())
        for i in range(self.count):
            sql = "insert into simple(x) values(%d)" % i
            deferredResult(trans.runOperation(sql))
        deferredResult(trans.commit())

        # we must now have 1 pooled connection and 0 transactions
        self.checkConnections(1)
        self.checkTransactions(0)

        # let's do the query
        trans = deferredResult(self.dbpool.begin())
        for i in range(self.count):
            sql = "select x from simple where x = %d" % i
            rows = deferredResult(trans.runQuery(sql))
            # remember, we did 2 inserts for every index
            self.failUnless(len(rows) == 2, "Too many results (insert error?)")
            self.failUnless(rows[0][0] == i, "Wrong result (insert error?)")
        deferredResult(trans.rollback())

        self.checkConnections(1)
        self.checkTransactions(0)     

        # now we generate an SQL error
        trans = deferredResult(self.dbpool.begin())
        
        self.checkConnections(0)
        self.checkTransactions(1)

        deferredError(trans.runQuery("select * from NOTABLE"))
        log.flushErrors()
        
        self.checkConnections(1)
        self.checkTransactions(0)
        
        trans = deferredResult(self.dbpool.begin())
        deferredError(trans.runOperation("delete from * from NOTABLE"))
        log.flushErrors()
        
        # let's check the rollback by deleting everything
        if self.can_rollback:
            trans = deferredResult(self.dbpool.begin())
            sql = "delete from simple"
            deferredResult(trans.runOperation(sql))
            deferredResult(trans.rollback())

            sql = "select count(1) from simple"
            row = deferredResult(self.dbpool.runQuery(sql))
            self.failUnless(int(row[0][0]) == 200, "Operation not rolled back")
            
            self.checkConnections(1)
            self.checkTransactions(0)

        # now really delete and then select in the same transaction
        trans1 = deferredResult(self.dbpool.begin())
        trans2 = deferredResult(self.dbpool.begin())

        sql = "delete from simple"
        deferredResult(trans1.runOperation(sql))

        # two different count checks
        sql = "select count(1) from simple"
        rows1 = deferredResult(trans1.runQuery(sql))
        rows2 = deferredResult(trans2.runQuery(sql))

        self.failUnless(rows1[0][0] == 0, "Operation failed?")
        if self.can_isolate:
            self.failUnless(rows2[0][0] == 200, "No isolation.")
        else:
            self.failUnless(rows2[0][0] == 0, "Unexpected isolation.")

        self.checkConnections(0)
        self.checkTransactions(2)

        deferredResult(trans1.commit())
        deferredResult(trans2.rollback())
        
        self.checkConnections(2)
        self.checkTransactions(0)

    def startDB(self): pass
    def stopDB(self): pass

class PostgresTestCase(XDBAPITestCase, unittest.TestCase):
    """Test cases for the SQL reflector using Postgres.
    """

    def makePool(self):
        return ConnectionPool('pyPgSQL.PgSQL', database=self.DB_NAME,
                              user=self.DB_USER, password=self.DB_PASS,
                              connmin=2, connmax=2)
			      
class PsycopgTestCase(XDBAPITestCase, unittest.TestCase):
    """Test cases for the SQL reflector using psycopg for Postgres.
    """

    def makePool(self):
        return ConnectionPool('psycopg', database=self.DB_NAME,
                              user=self.DB_USER, password=self.DB_PASS,
                              connmin=2, connmax=2)


class MySQLTestCase(XDBAPITestCase, unittest.TestCase):
    """Test cases using MySQL."""

    trailingSpacesOK = 0
    can_rollback = 0
    can_isolate = 0
    
    def makePool(self):
        return ConnectionPool('MySQLdb', db=self.DB_NAME,
                              user=self.DB_USER, passwd=self.DB_PASS,
                              connmin=2, connmax=2)


if PgSQL is None: PostgresTestCase.skip = "pyPgSQL module not available"
else:
    try:
        conn = PgSQL.connect(database=PostgresTestCase.DB_NAME,
                             user=PostgresTestCase.DB_USER,
                             password=PostgresTestCase.DB_PASS)
        conn.close()
    except Exception, e:
        PostgresTestCase.skip = "Connection to PgSQL server failed: " + str(e)
	
if psycopg is None: PsycopgTestCase.skip = "psycopg module not available"
else:
    try:
        conn = psycopg.connect(database=PostgresTestCase.DB_NAME,
                               user=PostgresTestCase.DB_USER,
                               password=PostgresTestCase.DB_PASS)
        conn.close()
    except Exception, e:
        PostgresTestCase.skip = \
            "Connection to PostgreSQL using psycopg failed: " + str(e)

if MySQLdb is None: MySQLTestCase.skip = "MySQLdb module not available"
else:
    try:
        conn = MySQLdb.connect(db=MySQLTestCase.DB_NAME,
                               user=MySQLTestCase.DB_USER,
                               passwd=MySQLTestCase.DB_PASS)
        conn.close()
    except Exception, e:
        MySQLTestCase.skip = "Connection to MySQL server failed: " + str(e)
