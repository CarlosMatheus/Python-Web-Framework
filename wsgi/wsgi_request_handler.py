from http.server import BaseHTTPRequestHandler
from wsgiref.handlers import SimpleHandler
import urllib.parse
import sys

VERSION = '0.1'


class ServerHandler(SimpleHandler):

    server_software = server_version = "WSGIServer/" + VERSION

    def close(self):
        try:
            self.request_handler.log_request(
                self.status.split(' ', 1)[0], self.bytes_sent
            )
        finally:
            SimpleHandler.close(self)


class WSGIRequestHandler(BaseHTTPRequestHandler):

    """
    This is a simple class to handle the HTTP requests
    It inherits from BaseHTTPRequestHandler Python standard library
    """

    server_version = "WSGIServer/" + VERSION

    @staticmethod
    def get_stderr():
        """
        Get standard error
        :return: python's system error
        """
        return sys.stderr

    def __init__(self, request, client_address, server):
        self.raw_requestline = str()
        self.requestline = str()
        self.request_version = str()
        self.command = str()
        super().__init__(request, client_address, server)

    def get_environ(self):
        """
        Will define the env parameter of the WSGI on a HTTP request
        :return: env parameter, it is a dictionary
        """

        env = self.server.base_environ.copy()
        env['SERVER_PROTOCOL'] = self.request_version
        env['SERVER_SOFTWARE'] = self.server_version
        env['REQUEST_METHOD'] = self.command

        """
        Will treat the query if any on the url
        """
        if '?' in self.path:
            path, query = self.path.split('?', 1)
        else:
            path, query = self.path, ''

        env['PATH_INFO'] = urllib.parse.unquote(path, 'iso-8859-1')
        env['QUERY_STRING'] = query

        host = self.address_string()
        if host != self.client_address[0]:
            env['REMOTE_HOST'] = host
        env['REMOTE_ADDR'] = self.client_address[0]

        if self.headers.get('content-type') is None:
            env['CONTENT_TYPE'] = self.headers.get_content_type()
        else:
            env['CONTENT_TYPE'] = self.headers['content-type']

        length = self.headers.get('content-length')
        if length:
            env['CONTENT_LENGTH'] = length

        for k, v in self.headers.items():
            # formatting headers
            k = k.replace('-', '_').upper()
            v = v.strip()

            if k in env:
                continue                    # skip content length, type,etc.
            if 'HTTP_'+k in env:
                env['HTTP_'+k] += ',' + v     # comma-separate multiple headers
            else:
                env['HTTP_'+k] = v

        return env

    def handle(self):
        """
        Handle a single HTTP request
        Following the specifications of WSGI handler
        """

        self.raw_requestline = self.rfile.readline(65537)
        if len(self.raw_requestline) > 65536:
            self.requestline = ''
            self.request_version = ''
            self.command = ''
            self.send_error(414)
            return

        # An error code has been sent, just exit
        if not self.parse_request():
            return

        handler = ServerHandler(
            self.rfile, self.wfile, self.get_stderr(), self.get_environ()
        )

        # back pointer for logging
        handler.request_handler = self
        handler.run(self.server.get_app())
