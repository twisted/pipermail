
class Node(object):
   
	value		#A sizeable object, usually a numpy array.
	timestamp	#An integer, incremented every time value is changed.
	parents		#The parent Nodes of self

    parent_timestamp_caches	# Remembered values of parents' timestamps the last n times
							# compute_prob() was called.

    prob_caches				# Remembered outputs of compute_prob() the last n times it
							# was called.
							
	# It turns out to be optimal to have n = 2.

	def compute_prob():
		"""
		A heavyweight function, should be called as little as possible.
		Returns a float value.
		"""
		return some_function([parent.value for parent in parents])

    def get_prob():
		"""
       	Check my parents' timestamps. 

		If this combination is present in parent_timestamp_caches, 
		return the appropriate value from prob_caches.
		
		Otherwise,
			- 	Call compute_prob()
			- 	Store this combination of parents' timestamps in
				parent_timestamp_caches
			-	Store the output of compute_prob() in prob_caches
			-	Return the output of compute_prob().
		"""