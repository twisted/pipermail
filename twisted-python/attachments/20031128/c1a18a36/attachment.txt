Reading the docs on the twisted web server I see that it automatically handles object publishing.  But what if I want to respond to requests that aren't based on a object structure?  IOW:

Client does a GET on:
localhost/infodir/subdir/doc.txt

in this case infodir, subdir, and doc.txt would actually be info to lookup in a database on the fly, no object structure.  Is this possible?

I hope I'm explaining myself ok...

Thanx for any ideas,

OLIVER

P.S. I'm looking at TWISTED because it supports DB connection pooling.


