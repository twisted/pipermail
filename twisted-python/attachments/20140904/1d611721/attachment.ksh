import gc
import objgraph
import os
import sqlite3
import sys

from time import sleep
from twisted.enterprise.adbapi import ConnectionPool
from twisted.internet import defer, task, reactor


def _removeFile(path):
    try:
        os.unlink(path)
    except OSError:
        pass


def plain_sqlite3(conn, rows):
    query = 'INSERT INTO t (value) VALUES (1)'

    cursor = conn.cursor()
    for row in range(rows):
        cursor.execute(query)

    cursor.close()
    conn.commit()
    


def adbapi(pool, rows):
    query = 'INSERT INTO tw (value) VALUES (2)'

    last = None
    for row in range(rows):
        last = pool.runOperation(query)
        last.addCallback(lambda _: None)

    return last


def inline_callbacks(pool, rows):
    query = 'INSERT INTO tw (value) VALUES (3)'

    @defer.inlineCallbacks
    def do_insert():
        for row in range(rows):
            deferred = pool.runOperation(query)
            deferred.addCallback(lambda _: None)
            yield deferred

    return do_insert()


def semaphore(pool, rows):
    query = 'INSERT INTO tw (value) VALUES (4)'

    semaphore = defer.DeferredSemaphore(1)
    last = None
    for row in range(rows):
        last = semaphore.run(pool.runOperation, query)
        last.addCallback(lambda _: None)

    return last


def cooperator(pool, rows):
    query = 'INSERT INTO tw (value) VALUES (5)'
    
    def generator():
        for row in range(rows):
            deferred = pool.runOperation(query)
            deferred.addCallback(lambda _: None)
            yield deferred

    cooperator = task.Cooperator()
    return cooperator.coiterate(generator())



def run(callable, repeats):
    _removeFile('test-sq3.db3')
    conn = sqlite3.connect('./test-sq3.db3')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE t (id ROWID, value INTEGER)')

    for step in range(repeats):
        print "Run #%d %s..." % (step, inserter)
        callable(conn, 2000)

    conn.close()    

    cursor = None
    conn = None


def run_twisted(callable, repeats):
    _removeFile('test-twisted.db3')
    pool = ConnectionPool('sqlite3', cp_min=1, cp_max=1, database='test-twisted.db3', check_same_thread=False)
    pool.runOperation('CREATE TABLE tw (id ROWID, value INTEGER)')

    last = None

    @defer.inlineCallbacks
    def execute():
        for step in range(repeats):
            print "Run #%d %s..." % (step, callable)
            last = callable(pool, 2000)
            yield last

        last.addCallback(lambda _: pool.close())
        last.addCallback(lambda _: reactor.stop())

    reactor.callWhenRunning(execute)
    reactor.run()
    
    last = None
    pool = None


gc.collect()
objgraph.show_growth()
    
#run(plain_sqlite3, 100)
#run_twisted(adbapi, 100)
#run_twisted(inline_callbacks, 100)
#run_twisted(semaphore, 100)
run_twisted(cooperator, 100)

print "Press ENTER to exit..."
sys.stdin.read(1)

gc.collect()
objgraph.show_growth()
