"""
This exemplify how a WSGI works
"""

# This is a function from a default python library that allow us to make a WSGI server.
from wsgiref.simple_server import make_server

from wsgi.web_server_gateway_interface import WebServerGatewayInterface


def web_app(environment, response):
    """
    A simple web app
    :param environment:
    :param response:
    :return:
    """
    print(environment['PATH_INFO'])
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    response(status, headers)

    f = open('./templates/index.html', 'r').read()

    return [f.encode()]


# Empty string means that the host will be local host
host = ''
port = 8080

# with make_server(host, port, web_app) as server:
#     if not host:
#         print("Serving on port %d \nVisit http://127.0.0.1:%d" % (port, port))
#     else:
#         print("Serving on port %d \nVisit http://%s:%d" % (port, host, port))
#     print("To kill the server enter 'control + c'")
#
#     # will server forever until we kill it
#     server.serve_forever()

with WebServerGatewayInterface(host, port, web_app) as server:
    if not host:
        print("Serving on port %d \nVisit http://127.0.0.1:%d" % (port, port))
    else:
        print("Serving on port %d \nVisit http://%s:%d" % (port, host, port))
    print("To kill the server enter 'control + c'")

    # will server forever until we kill it
    server.serve_forever()

