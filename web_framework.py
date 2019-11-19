from wsgi.web_server_gateway_interface import WebServerGatewayInterface


class WebFramework:
    def __init__(self):
        self.routes = dict()

    def __call__(self, environ, response):
        body = self.handle_request(environ)

        status = '200 OK'
        headers = [('Content-type', 'text/html; charset=utf-8')]

        response(status, headers)

        return [body.encode()]

    def start_server(self, host='', port=8080):
        with WebServerGatewayInterface(host, port, self) as server:
            if not host:
                print("Serving on port %d \nVisit http://127.0.0.1:%d" % (port, port))
            else:
                print("Serving on port %d \nVisit http://%s:%d" % (port, host, port))
            print("To kill the server enter 'control + c'")
            server.serve_forever()

    def route(self, path):
        def wrapper(handler):
            self.routes[path] = handler
            return handler

        return wrapper

    def handle_request(self, request):

        request_path = request['PATH_INFO']

        if request_path in self.routes:
            response = self.routes[request_path](request)
        else:
            print("Route " + request_path + " not found")
            response = "Page not found"

        return response
