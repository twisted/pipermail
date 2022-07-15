"""Parallelise X items from a set, keeping no more than count items active"""
from twisted.internet import defer

def parallel( iterable, count, callable, *args, **named ):
	"""Run count instances of callable in parallel until all finished
	
	Usage:
		pd = parallel.parallel( 
			modems.keys(), 
			5,
			self.processModem,
			modems = modems,
			done = done,
		)
		
		iterable -- produce argument for each call
		count -- number of "parallel" operations to start
		callable -- callable function:
		
			callable( currentValue, *args, **named )
			
			Must return a Deferred instance 
		args, named -- extra parameters for callable
		
	returns a DeferredList with one deferred for each item in iterable

	Note:
		If you need to know how many iterations have been started, you'll
		have to handle that manually.
	"""
	dl = []
	sem = defer.DeferredSemaphore(count)
	def onFinished( result ):
		"""Allow the next item to continue processing"""
		sem.release()
		return result
	def onAcquire( sem, item ):
		"""Dispatch the next item from iterable to callable"""
		try:
			return callable( item, *args, **named ).addCallbacks( 
				onFinished, onFinished 
			)
		except Exception, err:
			# if count items fail we still want to continue processing, not
			# hang waiting to return...
			sem.release()
			raise
	for item in iterable:
		df = sem.acquire().addCallback( onAcquire, item=item )
		dl.append( df )
	if dl:
		return defer.DeferredList( dl )
	else:
		return defer.succeed( dl )
