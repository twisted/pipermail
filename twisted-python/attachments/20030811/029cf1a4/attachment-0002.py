from twisted.web.woven import model, page, interfaces
from twisted.python import components

template = """
<html>
<body>
    <ul view='List'>
        <li pattern='listItem'><a view='Text'>Sample List Item</a></li>
    </ul>
</body>
</html>
"""

class StringWithChildren(str):
    def __init__(self, value):
        str.__init__(value)
        self.children = []


class StringModelWithChildren(model.StringModel):
    def getSubmodel(self, request=None, name=None):
        if name == 'children':
            return model.ListModel(self.original.children)
        else:
            return model.StringModel.getSubmodel(self, request, name)

components.registerAdapter(StringModelWithChildren, StringWithChildren, interfaces.IModel)

data = []
for item in ["One", "Two", "Three"]:
    data.append(StringWithChildren(item))
data[1].children = [StringWithChildren(item) for item in ['Two.One', 'Two.Two', 'Two.Three', 'Two.Four']]
data[1].children[1].children.append("Two.Two.One")

myPage = page.Page(data, template=template)
resource = myPage

if __name__ == "__main__":
    from twisted.web import server
    from twisted.internet import reactor
    mySite = server.Site(resource)
    reactor.listenTCP(8009, mySite)
    reactor.run()
