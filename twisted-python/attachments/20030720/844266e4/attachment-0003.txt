from twisted.web.woven import page

class MyPage(page.Page):
	template = """
	<html>
		Root Page
		<p>
			<a href="fred">Fred</a>
		</p>
		<p>
			<a href="bob">Bob</a>
		</p>
	</html>
	"""              
	def wchild_fred(self, request):
		return page.Page(template="<html>Fred!</html>")

	def wchild_bob(self, request):
		return page.Page(template="<html>Bob!</html>")

resource = MyPage()
