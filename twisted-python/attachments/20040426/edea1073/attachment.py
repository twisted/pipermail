from twisted.enterprise import adbapi
from twisted.internet import reactor
from twisted.python import log

def getCount():
	return dbpool.runQuery("select count(*) from test")


def printCount(r):
	if r:
		print "Count: ", r[0][0]
	else:
		print "No count"

dbpool = adbapi.ConnectionPool("pyPgSQL.PgSQL", database="test", user="test", password = 'test')

getCount().addCallback(printCount).addErrback(log.err)

reactor.iterate(2)
#reactor.run()
