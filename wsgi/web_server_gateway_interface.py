from wsgi.wsgi_request_handler import WSGIRequestHandler
from wsgi.wsgi_http_server import WSGIHTTPServer

"""
I did not found on internet any tutorial regarding how to create a WSGI itself, all tutorials were about how to use it
that might happen due to the fact that WSGI are very standard as a protocol.

So in order to create my own implementation of a WSGI I had to look at the ones that alredy exits
By exploring the documentation of  and wsgiref
"""


class WebServerGatewayInterface:

    def __init__(self, host, port, app):
        self.host = host
        self.port = port
        self.app = app

    def __enter__(self):
        """
        Will be called when using the "with" python call
        :param host: the host ip address
        :param port: the host port
        :param app: the app that will run the web framework
        """
        self.server = WSGIHTTPServer((self.host, self.port), WSGIRequestHandler)
        self.server.setup_app(self.app)
        return self.server

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.server.shutdown()
