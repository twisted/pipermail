from twisted.web import resource, server
from twisted.python import formmethod
from twisted.web.woven import view, form, page

def plusOne(number):
	return number+1

plusOneSignature = formmethod.MethodSignature(
	formmethod.Integer("number", allowNone=0, shortDesc="Number"),
	)

template = """
<html>
    <head><title>My Form</title></head>
    <body>
        <h1>Test Form</h1>
    	<form method='get' action='process' model='.' view=''></form>
    </body>
</html>
"""

class FormPage(page.Page):
    def getChild(self, name, request):
        if name=='process':
            return form.FormProcessor(plusOneSignature.method(plusOne), 
                    callback=showResults,
                    errback=lambda model: view.View(model, template=template)
                    )
        else:
            return page.Page.getChild(self, name, request)

def showResults(returnVal):
    results = resource.Resource()
    results.render = lambda *args: str(returnVal)
    return results

data = formmethod.FormMethod(plusOneSignature, plusOne)

formDemoPage = FormPage(data, template=template)
website = server.Site(formDemoPage)

from twisted.internet import app
application = app.Application("formtest")
application.listenTCP(8018, website)

if __name__ == '__main__':
	application.run(save=False)
