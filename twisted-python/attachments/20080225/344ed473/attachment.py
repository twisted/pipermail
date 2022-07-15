from twisted.trial import unittest
from twisted.mail import smtp

def evenIfCallbackIsCalled(*args):
   return True

class Test1(unittest.TestCase):
   def test_sendmail(self):

      return smtp.sendmail('localhost', 'foo@bar.pl', 'dotz@localhost',
                           'this leaves reactor dirty :-(').addCallback(evenIfCallbackIsCalled)
