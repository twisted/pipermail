from nevow import tags as T
from nevow import rend, loaders

class MyPage(rend.Page):
    docFactory = loaders.htmlstr("""
    <html><head><title>Nested Maps Sequence Rendering</title></head>
        <body>
            <ul nevow:data="dct" nevow:render="sequence">
                <li nevow:pattern="item" nevow:render="mapping">
                    <span><nevow:slot name="name">Name</nevow:slot></span>
                    <span><nevow:slot name="surname">Surname</nevow:slot></span>
                    <span><nevow:slot name="age">Age</nevow:slot></span>
                    <nevow:invisible nevow:render="html description" />
                </li>
            </ul>
        </body>
    </html>
    """)
    def __init__(self, dct):
        self.data_dct = dct
        rend.Page.__init__(self)

    def render_html(self, key):
        """
        Render the given key as xml/html instead of escaping it as text.
        """
        def _(ctx, data):
            if key in data:
                return ctx.tag[T.xml(data[key])]
            return ""
        return _

dct = [
    {'name':'Mark', 'surname':'White', 'age':'45', 
        'description': '<div style="color:red">Hello World</div><div style="color:blue">whatever</div>'},
    {'name':'Valentino', 'surname':'Volonghi', 'age':'21'},
    {'name':'Peter', 'surname':'Parker', 'age':'Unknown',
        'description': '<div style="color:blue">Hello World</div><div style="color:red">whatever</div>'}
]


if __name__ == "__main__":
   print MyPage(dct).renderSynchronously()



