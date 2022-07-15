2006/07/16 16:16 GMT [-] Log opened.
2006/07/16 16:16 GMT [-] twistd 2.2.0 (C:\Python2.4\python.exe 2.4.3) starting up
2006/07/16 16:16 GMT [-] reactor class: twisted.internet.selectreactor.SelectReactor
2006/07/16 16:16 GMT [-] nevow.appserver.NevowSite starting on 8080
2006/07/16 16:16 GMT [-] Starting factory <nevow.appserver.NevowSite instance at 0x01158648>
2006/07/16 16:16 GMT [HTTPChannel,0,127.0.0.1] Traceback (most recent call last):
	  File "C:\Python2.4\Lib\site-packages\nevow\rend.py", line 546, in _renderHTTP
	    return self.flattenFactory(doc, ctx, writer, finisher)
	  File "C:\Python2.4\Lib\site-packages\nevow\rend.py", line 506, in <lambda>
	    flattenFactory = lambda self, *args: flat.flattenFactory(*args)
	  File "C:\Python2.4\Lib\site-packages\nevow\flat\__init__.py", line 14, in flattenFactory
	    return deferflatten(stan, ctx, writer).addCallback(finisher)
	  File "C:\Python2.4\Lib\site-packages\nevow\flat\twist.py", line 37, in deferflatten
	    drive()
	--- <exception caught here> ---
	  File "C:\Python2.4\Lib\site-packages\nevow\flat\twist.py", line 17, in drive
	    next = iterable.next()
	  File "C:\Python2.4\Lib\site-packages\nevow\flat\ten.py", line 84, in iterflatten
	    for item in gen:
	  File "C:\Python2.4\Lib\site-packages\nevow\flat\flatstan.py", line 89, in TagSerializer
	    newdata = convertToData(original.data, context)
	  File "C:\Python2.4\Lib\site-packages\nevow\accessors.py", line 30, in convertToData
	    newdata = olddata.get(context)
	  File "C:\Python2.4\Lib\site-packages\nevow\accessors.py", line 52, in get
	    child = container.child(context, self.original.name)
	  File "C:\Python2.4\Lib\site-packages\nevow\accessors.py", line 128, in child
	    return self.original[int(name)]
	exceptions.ValueError: invalid literal for int(): option_list
	
2006/07/16 16:16 GMT [HTTPChannel,0,127.0.0.1] 127.0.0.1 - - [16/Jul/2006:18:16:45 +0000] "GET / HTTP/1.1" 500 12253 "-" "Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.0.4) Gecko/20060508 Firefox/1.5.0.4"
2006/07/16 16:16 GMT [-] Received SIGINT, shutting down.
2006/07/16 16:16 GMT [-] (Port 8080 Closed)
2006/07/16 16:16 GMT [-] Stopping factory <nevow.appserver.NevowSite instance at 0x01158648>
2006/07/16 16:16 GMT [-] Main loop terminated.
2006/07/16 16:16 GMT [-] Server Shut Down.
