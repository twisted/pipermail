from twisted.application import internet, service
from nevow import appserver, inevow, rend, compy, loaders, url
from nevow import tags as T

class Menu(object):
    def __init__(self, title, *items):
        self.title = title
        self.items = items

class MenuItem(object):
    def __init__(self, title, target):
        self.title = title
        self.target = target

class MenuView(compy.Adapter):
    __implements__ = inevow.IRenderer

    def rend(self, data):
        items = getattr(self.original, 'items')
        return T.div[
                   T.p[getattr(self.original, 'title')],
                   T.ul[[T.li[x] for x in items]]
               ]

class MenuItemView(compy.Adapter):
    __implements__ = inevow.IRenderer

    def rend(self, data):
        target = getattr(self.original, 'target')
        return T.a(href=getattr(self.original, 'title'))[target]

compy.registerAdapter(MenuView, Menu, inevow.IRenderer)
compy.registerAdapter(MenuItemView, MenuItem, inevow.IRenderer)

# some data
menu = Menu('Main Menu',
            Menu('Item 1',
                 MenuItem('1-1', url.root.child('oneone')),
                 MenuItem('1-2', url.root.child('onetwo')),
                 ),
            MenuItem('2', url.root.child('two')),
            MenuItem('3', url.root.child('three'))
            )


class Page(rend.Page):
    def render_menu(self, context, data):
        return inevow.IRenderer(data)

    def data_menu(self, context, data):
        return menu

    docFactory = loaders.stan(
    T.html[
        T.body[
            T.invisible(render=T.directive('menu'), data=T.directive('menu'))
        ]
    ])

site = appserver.NevowSite(Page())
application = service.Application("menu")
httpd = internet.TCPServer(8000, site).setServiceParent(application)
