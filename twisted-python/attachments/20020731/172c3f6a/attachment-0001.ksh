<html>
<head>
<meta http-equiv="Content-Type" content="text/html;  charset=ISO-8859-1" />
<title>Controller</title>

<script language="JavaScript1.2" src="/conduit.js">
</script>

</head>
<body bgcolor="#FFFFFF" onload="focusInput()">

<div id="content" style="border: green solid 1px; width: 100%;">
</div>

<input type="text" id="inputText" />
<input type="button" value="Send" onclick="send(document.getElementById('inputText').value)" />

<br />
<span style="width: 45%">Input</span>
<span style="width: 45%">Output</span>
<br />
<iframe id="input" src="/input.html" style="width: 45%; height: 48pt">
</iframe>
<iframe id="output" src="?output=1" style="width: 45%; height: 48pt">
</iframe>

</body>
</html>
