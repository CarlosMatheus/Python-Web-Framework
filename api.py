from webob import Request, Response


class API:
    def __init__(self):
        self.routes = dict()

    def __call__(self, environ, start_response):
        request = Request(environ)

        response = Response()
        response.text = "Hello, World!"

        return response(environ, start_response)

    def route(self, path):
        def wrapper(handler):
            self.routes[path] = handler
            return handler

        return wrapper

    def handle_request(self, request):
        user_agent = request.environ.get("HTTP_USER_AGENT", "No user agent found")

        response = Response()
        response.text = f"Hello, my friend with this user agent: {user_agent}"

        return response

