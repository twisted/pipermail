"""Parallelise X items from a set, keeping no more than count items active"""
from twisted.internet import reactor, defer
from twisted.python import failure

class Parallel( object ):
	"""Class managing parallel dispatch across items in an iterable
	
	Usage is intended to look very much like a DeferredList, save that 
	items are dispatched so that no more than a given number are active
	at any given time, so that the system doesn't bog down processing
	a large number of items from the iterable.
	
	For instance, if you need to process 10,000 items with a database 
	operation, you often do *not* want to dispatch all 10,000 database 
	operations, as then any interactive operations will have to wait for 
	all 10,000 to complete before the system can respond to a user query.
	
	There probably is *something* in Twisted core that can do this (I even
	have a rough memory of reading about it), I just couldn't find it when 
	I went looking.
	
		p = parallel.Parallel( 
			modems.keys(), 
		)
		return p( 
			self.batchSize,
			self.processModem,
			modems = modems,
			parallelObject = p,
		)
	
	or, more concisely, for when you don't need the Parallel object for
	display of progress bars or the like:

		return parallel.Parallel( 
			modems.keys(), 
		)( 
			self.batchSize,
			self.processModem,
			modems = modems,
			parallelObject = p,
		)
		
	Attributes:
		dispatched -- count of items dispatched 
		returned -- count of items which have completed 
		allDispatched -- whether all items have been dispatched 
		allReturned -- whether all items have completed
		finalDF -- the final deferred object we will call
		iterable -- iterable which produces our items
		callable -- the callable object we will apply to items from iterable 
		args, named -- extra arguments to callable 

	Note:
		Despite being broken into initialisation and call steps, you
		should *not* treat a Parallel object as reentrant, they are 
		*not* able to be restarted reliably.
		
	XXX confirm proper operation when iterable is empty...
	"""
	dispatched = 0
	returned = 0
	allDispatched = False 
	allReturned = False
	finalDF = None
	def __init__( self, iterable ):
		"""Setup the parallel dispatcher
		
		iterable -- produce argument for each call
		"""
		self.iterable = iter(iterable)
		self.live = []
	def __call__( self, count, callable, *args, **named ):
		"""Call the parallel dispatcher, dispatching count items in parallel
		
		count -- number of "parallel" operations to start
		callable -- callable function:
		
			callable( currentValue, *args, **named )
			
			Must return a Deferred instance 
		args, named -- extra parameters for callable
		
		The reason we have callable, args and named specified here is that we
		often want access to the ParallelDispatcher instance in the arguments 
		to the iterable function (to calculate fraction completed, for instance).
		
		returns deferred returning [(success,result) for item in self.iterable]
		"""
		self.callable = callable 
		self.args = args 
		self.named = named 
		if self.finalDF is None:
			self.finalDF = defer.Deferred()
		# We could raise an error here, but this allows us to later decide to
		# kick off a few *extra* parallel operations, should we desire that...
		for x in range( count ):
			if not self.next():
				break
		return self.finalDF
	def next( self ):
		"""Iterate to schedule the next item"""
		try:
			try:
				value = self.iterable.next()
			except (StopIteration,IndexError), err:
				self.allDispatched = True
				if self.dispatched == 0:
					self.allReturned = True
					if self.finalDF:
						self.finalDF.callback( self.live )
						self.cleanup()
				return False
			else:
				df = self.callable( value, *self.args, **self.named )
				index = self.dispatched
				self.dispatched += 1
				self.live.append( None )
				if not hasattr( df, 'addCallbacks' ):
					raise TypeError(
						"""Callable %r (with arguments) (%s,%s) did not return a Deferred (no addCallbacks method): %r"""%(
							self.callable,
							", ".join( [str(x) for x in (value,) + self.args] ),
							", ".join( ["%s=%r"%(key,value) for key,value in self.named.items()] ),
							df,
						)
					)
				df.addCallbacks( 
					self.oneFinished, self.oneFailed, 
					callbackKeywords={'index':index},
					errbackKeywords={'index':index},
				)
				return True
		except Exception, err:
			self.finalDF.errback( failure.Failure())
	def doNext( self ):
		"""Decide whether to dispatch another request"""
		if self.allDispatched:
			if self.returned >= self.dispatched:
				self.allReturned = True
				self.finalDF.callback( self.live )
				self.cleanup()
		else:
			self.next()
	def oneFailed( self, reason, index ):
		"""Retire one of our items"""
		self.returned += 1
		self.live[index] = (False, reason)
		self.doNext()
	def oneFinished( self, result, index ):
		"""Retire one of our items"""
		self.returned += 1
		self.live[index] = (True, result)
		self.doNext()
	def cleanup( self ):
		"""Eliminate all of our potentially circular references"""
		try:
			del self.callable
			del self.args 
			del self.named
			del self.iterable
			del self.finalDF
		except AttributeError, err:
			pass
