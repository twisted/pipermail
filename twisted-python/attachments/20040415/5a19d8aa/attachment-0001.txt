Dear all,
I am implementing a pseudo-shell application in python that communicates with a database-like server.
I have been tinkering with twisted for a few weeks and am impressed - I could make a client and imitate the server with a small amount of clean python code!
However, I'm not sure how to use twisted (or if it can be done) to do the kind of application I want to do.

Specifically, the application will take input from the user or from a file, just like a normal shell, then communicate with the server behind this. I'm sure this is a very well known problem, but I'm not sure where to start - threads? twisted? select-loop?

In my app the user will see something like this:

  myshell$ select * from data
  results:
  id       title
  123    Foo
  456    Bar

  myshell$ 

and so on.

But after typing the select statement, THATS when I want to utilize the power of twisted to send a buffer to the server, then wait for the response and unpack it.

To complicate things, the server sends async announcments of change events, e.g. new rows in the database. I want to be able to handle these while still receiving user input (eg print them on the console)

I've got a basic interactive shell going on its own no probs, and as mentioned I've got a separate basic twisted client going too.

Can anyone point me at examples or tips on how to use twisted for handling the socket comms and still allow interactivity with the user?

Thanks - and hope this isn't a really silly question!
Ellers



