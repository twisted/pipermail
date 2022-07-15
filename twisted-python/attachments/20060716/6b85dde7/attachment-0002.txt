from twisted.application import service, strports

from nevow import appserver, rend, loaders



class Main(rend.Page):
    addSlash = True
    docFactory = loaders.xmlfile('nestedsequence.xhtml')
    
    def __init__(self):
        # cached
        self.data_option_list = [('1', 'uno'), ('2', 'due')]

    def data_control_list(self, ctx, data):
        return [('a', 'first'),  ('b', 'second')]

    def render_control(self, ctx, data):
        ctx.fillSlots('ctrl_label', data[1])
        ctx.fillSlots('ctrl_name', data[0])
 
        return ctx.tag

    def render_option(self, ctx, data):
        ctx.fillSlots('opt_label', data[1])
        ctx.fillSlots('opt_value', data[0])

        return ctx



application = service.Application("nested sequence")
site = appserver.NevowSite(Main())

addr = "tcp:8080:interface=127.0.0.1"
strports.service(addr, site).setServiceParent(application)

