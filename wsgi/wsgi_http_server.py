from http.server import HTTPServer


class WSGIHTTPServer(HTTPServer):
    """"""
    """
    This class inherit from HTTPServer Python standard class
    This class is basically a basic HTTP Server that implements the Python WSGI protocol
    
    > HTTPServer will basically create and listen at an HTTP socket, 
    sending the requests for a handler that the WebServerGatewayInterface will define.
    """
    """
    This implementation uses the CGI 1.1 (Common Gateway Interface) from the HTTPServer according with RFC 3875
    The RFC 3875 states what is and who will a CGI/1.1 work on HTTP Servers
    """

    # the web framework that will handle the HTTP requests
    application = None

    def __init__(self, server_address, request_handler_class):
        """
        Constructor that also calls the HTTPServer constructor
        :param server_address: tuple (IP, port)
        :param request_handler_class: A class that will handle the HTTP requests
        """

        # environ with definitions of the HTTP server
        self.base_environ = dict()

        super().__init__(server_address, request_handler_class)

    def server_bind(self):
        """
        Override server_bind to store the server name.
        """
        HTTPServer.server_bind(self)
        self.setup_environ()

    def setup_environ(self):
        """
        Set up base environment
        """
        env = self.base_environ = {}
        env['SERVER_NAME'] = self.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PORT'] = str(self.server_port)
        env['REMOTE_HOST'] = ''
        env['CONTENT_LENGTH'] = ''
        env['SCRIPT_NAME'] = ''

    def setup_app(self, app):
        """
        setup the application
        this must be done by the WSGI
        :param app: the application reference, basically the framework that uses this WSGI
        """
        self.application = app

    def get_app(self):
        """
        Get the application reference
        """
        return self.application
