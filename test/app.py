"""
This exemplify how a WSGI works
"""

# This is a function from a default python library that allow us to make a WSGI server.
from wsgiref.simple_server import make_server


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

    return [b'<strong> Hello World I just created my first WSGI</strong>']


# Empty string means that the host will be local host
host = ''
port = 8080

with make_server(host, port, web_app) as server:
    if not host:
        print("Serving on port %d \nVisit http://127.0.0.1:%d" % (port, port))
    else:
        print("Serving on port %d \nVisit http://%s:%d" % (port, host, port))
    print("To kill the server enter 'control + c'")

    # will server forever until we kill it
    server.serve_forever()


