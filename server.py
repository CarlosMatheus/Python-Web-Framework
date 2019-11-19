from web_framework import WebFramework

server = WebFramework()


@server.route("/")
def home(request):
    return "Hello from the HOME page"


@server.route("/about")
def about(request):
    return "Hello from the ABOUT page"


server.start_server()
