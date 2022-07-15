# -*- python -*-

from nevow import rend
from nevow.tags import *

try:
    import formless
    from formless.webform import renderForms
except ImportError:
    from nevow import formless
    from nevow.freeform import renderForms
    
class IMyObject(formless.TypedInterface):
    def someMethod(
        self,
        one = formless.String(),
        two = formless.Choice(choicesAttribute='choices_two'),
        three = formless.Text(),
        ):
        """Some random method
        """
    someMethod = formless.autocallable(someMethod)

class MyObject(object):
    __implements__ = IMyObject,
    
    one = 'Default One'
    two = 'Choice3'
    three = 'Oh yeah.\nYou know how we do it.'
    
    choices_two = ['Choice1', 'Choice2', 'Choice3', 'Choice4']

    def someMethod(self, one, two, three):
        print 'someMethod:', one, two, three
        self.one = one
        self.two = two
        self.three = three

class FormPage(rend.Page):
    docFactory = rend.htmlstr('''
    <html>
    <body>
      <h1>A Test</h1>
      <div nevow:render="edit"></div>
    </body>
    </html>
    ''')
    
    def __init__(self):
        rend.Page.__init__(self, MyObject())
        self.myObject = MyObject()
        
    def configurable_myobject(self, ctx):
        return self.myObject

    def render_edit(self, ctx, data):
        return [
            h2[ 'self.original' ],
            renderForms(),
            h2[ 'self.myObject' ],
            renderForms('myobject'),
            ]



# for twistd

from twisted.application import service
from twisted.application import internet
from nevow import appserver

application = service.Application("mb-defaults")
internet.TCPServer(
    8080, 
    appserver.NevowSite(
        FormPage()
    )
).setServiceParent(application)

# for running standalone

if __name__ == '__main__':
    def printResult(result):
        print result
    FormPage().renderString().addCallback(printResult)
