from web_framework import WebFramework

server = WebFramework()


@server.route("/")
def home(request, method, query):
    print(request['REQUEST_METHOD'])
    print(request['CONTENT_TYPE'])
    return "Hello from the HOME page"


@server.route("/about")
def about(request, method, query):
    return server.open_template('index')


server.start_server()
