function onkeyevent(theEvent)
{ 	
    if (!theEvent) {
        theEvent = event
    }
	code = theEvent.keyCode;
	if (code==13) {
		var inputText = document.getElementById('inputText')
		send(inputText.value)
	}
}

function send(stuff) {
    if (stuff) {
        document.getElementById("input").src = "?input=" + escape(stuff)
        write("-> " + stuff)
        var inputText = document.getElementById("inputText")
        inputText.value = ""
        inputText.focus()
    }
}

function recv(stuff) {
    var output = document.getElementById("content")
// Works on ie mac and mozilla but not as well on ie win
//    output.appendChild(document.createTextNode(unescape(stuff)))
//    output.appendChild(document.createElement("br"))
// Works on ie win & mac, and mozilla, but is a bit slower
    output.innerHTML = output.innerHTML + unescape(stuff) + '<br \>'
    window.scrollBy(0, window.innerHeight)
}

function focusInput() {
    document.getElementById('inputText').focus()
}

document.onkeypress = onkeyevent
