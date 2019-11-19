from wsgi.web_server_gateway_interface import WebServerGatewayInterface
from os.path import join, isfile


class WebFramework:

    is_templates_routes = {'images', 'styles'}.__contains__

    def __init__(self):
        self.routes = dict()

    def __call__(self, environ, response):
        body = self.handle_request(environ)

        status = '200 OK'
        headers = [('Content-type', 'text/html; charset=utf-8')]

        response(status, headers)

        if hasattr(body, 'encode'):
            return [body.encode()]
        else:
            return [body]

    @staticmethod
    def open_template(name):
        f = open(join('templates', name) + '.html', 'r').read()
        return f

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

    def get_template(self, lt):
        file = join(lt[1], lt[2])
        file = join('templates', file)
        if isfile(file):
            f = open(file, 'rb').read()
        else:
            f = b''
        return f

    def handle_request(self, request):

        response = ""

        request_path = request['PATH_INFO']

        lt = request_path.split('/')

        if len(lt) > 2:
            first_part = lt[1]
            if self.is_templates_routes(first_part):
                response = self.get_template(lt)
        else:
            if request_path in self.routes:
                response = self.routes[request_path](request)
            else:
                print("Route " + request_path + " not found")
                response = "Page not found"

        return response
