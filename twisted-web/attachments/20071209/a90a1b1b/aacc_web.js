
// import Nevow.Athena

function keypress(event)
{
    var key = event.charCode ? event.charCode : event.keyCode;
    //var node = $("termid");
    //var widget = Nevow.Athena.Widget.get(node);
    var widget = Nevow.Athena.Widget.fromAthenaID("termid");
    if (widget) {
        alert("widget get ok");
        widget.callRemote("aacc_keypress", event.charCode, event.keyCode, event.metaKey, event.altKey, event.ctrlKey, event.shiftKey);
    }
    else {
        alert("widget get error");
    }
}

AaccWeb.Users = Nevow.Athena.Widget.subclass("AaccWeb.Users");
AaccWeb.Users.methods(

    function keypress2(self, event)
    {
        var key = event.charCode ? event.charCode : event.keyCode;
        self.callRemote("aacc_keypress", event.charCode, event.keyCode, event.metaKey, event.altKey, event.ctrlKey, event.shiftKey);
    },

    function start(self, node, event) {
        self.callRemote("aacc_start");
        return false;
    },

    function showConference(self, toWhat) {
        var client_data = Nevow.Athena.NodeByAttribute(self.node, "class", "Users");
        client_data.innerHTML = toWhat;
    }
);