from web_framework import WebFramework

server = WebFramework()


@server.route("/")
def home(request, method, query):
    # Simple response test
    return "Hello from the HOME page"


@server.route("/put_test_route")
def put_test_route(request, method, query):
    # Test different methods
    if method == server.methods.put:
        print('See that you are in fact using a PUT method')
        print(method)
        print('Received query:')
        print(query)
        return "Hello from the put_test_route page"
    else:
        return "Error: not put method"


@server.route("/about")
def about(request, method, query):
    # Test usage of HTTP templates
    return server.open_template('index')


server.start_server()
