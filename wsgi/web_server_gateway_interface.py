from wsgi.wsgi_request_handler import WSGIRequestHandler
from wsgi.wsgi_http_server import WSGIHTTPServer

"""
I did not found on internet any tutorial regarding how to create a WSGI itself, all tutorials were about how to use it
that might happen due to the fact that WSGI are very standard as a protocol.

So in order to create my own implementation of a WSGI I had to look at the ones that alredy exits
By exploring the documentation of  and wsgiref
"""


class WebServerGatewayInterface:
    def __enter__(self, host, port, app):
        """
        Will be called when using the "with" python call
        :param host: the host ip address
        :param port: the host port
        :param app: the app that will run the web framework
        """
        server = WSGIHTTPServer((host, port), WSGIRequestHandler)
        server.setup_app(app)
        return app
