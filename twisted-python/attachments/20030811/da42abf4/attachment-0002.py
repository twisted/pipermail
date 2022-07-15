from twisted.web.woven import page
from twisted.web.woven.widgets import List, appendModel

class Tree(List):
    def _iterateData(self, parentNode, submodel, data):
        currentListItem = 0
        retVal = [None] * len(data)
        for itemNum in range(len(data)):
            newNode = self.getPattern('listItem')
            if newNode.getAttribute('model') == '.':
                newNode.removeAttribute('model')
            elif not newNode.attributes.get("view"):
                newNode.attributes["view"] = self.defaultItemView
            appendModel(newNode, "%i/0" % itemNum)
            retVal[itemNum] = newNode
            newNode.parentNode = parentNode
            if data[itemNum][1]:
                newParent = self.templateNode.cloneNode(1)
                newParent.attributes['model'] = '../1'
                newNode.appendChild(newParent)                
                self._iterateData(newParent, "", data[itemNum][1])
        parentNode.childNodes.extend(retVal)


template = """
<html>
<body>
    <ul view='Tree'>
        <li pattern='listItem'><span view='Text'>Sample List Item</span></li>
    </ul>
</body>
</html>
"""

data = [
        ["One", []],
        ["Two", [
            ["Two.One", []],
            ["Two.Two", [
                ["Two.Two.One", []],
                ["Two.Two.Two", []],
                ["Two.Two.Three", []],
            ]],
            ["Two.Three", []],
        ]],
        ["Three", []],
    ]

myPage = page.Page(data, template=template)
myPage.setSubviewFactory("Tree", Tree)
resource = myPage

if __name__ == "__main__":
    from twisted.web import server
    from twisted.internet import reactor
    mySite = server.Site(resource)
    reactor.listenTCP(8009, mySite)
    reactor.run()
