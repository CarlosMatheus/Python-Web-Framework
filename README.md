# Python-Web-Framework
An HTTP Python web framework implementation that supports routering and templates like flask.

> Project in early development stage, not stable for production :construction:  

## Usage 

Create a `server.py` file as on the example of this repository.

On the file import the `WebFramework` class.

Define the routes and pages.

The framework also supports templates files similarly to flask, put them on templates folder.

Call the `start_server()` method at the end and run the `server.py` file.

## Example

```python
from web_framework import WebFramework

server = WebFramework()


@server.route("/")
def home(request):
    return "Hello from the HOME page"


@server.route("/about")
def about(request):
    return server.open_template('index')


server.start_server()
```


