import sys
import os
import re


_is_request = {
    'SCRIPT_NAME', 'PATH_INFO', 'QUERY_STRING', 'REQUEST_METHOD', 'AUTH_TYPE',
    'CONTENT_TYPE', 'CONTENT_LENGTH', 'HTTPS', 'REMOTE_USER', 'REMOTE_IDENT',
}.__contains__


def _needs_transcode(k):
    return _is_request(k) or k.startswith('HTTP_') or k.startswith('SSL_') \
        or (k.startswith('REDIRECT_') and _needs_transcode(k[9:]))


def is_hop_by_hop(header_name):
    """Return true if 'header_name' is an HTTP/1.1 "Hop-by-Hop" header"""
    _hoppish = {
        'connection': 1, 'keep-alive': 1, 'proxy-authenticate': 1,
        'proxy-authorization': 1, 'te': 1, 'trailers': 1, 'transfer-encoding': 1,
        'upgrade': 1
    }.__contains__
    return _hoppish(header_name.lower())


def read_environ():
    """Read environment, fixing HTTP variables"""
    enc = sys.getfilesystemencoding()
    esc = 'surrogateescape'
    try:
        ''.encode('utf-8', esc)
    except LookupError:
        esc = 'replace'
    environ = {}

    # Take the basic environment from native-unicode os.environ. Attempt to
    # fix up the variables that come from the HTTP request to compensate for
    # the bytes->unicode decoding step that will already have taken place.
    for k, v in os.environ.items():
        if _needs_transcode(k):

            # On win32, the os.environ is natively Unicode. Different servers
            # decode the request bytes using different encodings.
            if sys.platform == 'win32':
                software = os.environ.get('SERVER_SOFTWARE', '').lower()

                # On IIS, the HTTP request will be decoded as UTF-8 as long
                # as the input is a valid UTF-8 sequence. Otherwise it is
                # decoded using the system code page (mbcs), with no way to
                # detect this has happened. Because UTF-8 is the more likely
                # encoding, and mbcs is inherently unreliable (an mbcs string
                # that happens to be valid UTF-8 will not be decoded as mbcs)
                # always recreate the original bytes as UTF-8.
                if software.startswith('microsoft-iis/'):
                    v = v.encode('utf-8').decode('iso-8859-1')

                # Apache mod_cgi writes bytes-as-unicode (as if ISO-8859-1) direct
                # to the Unicode environ. No modification needed.
                elif software.startswith('apache/'):
                    pass

                # Python 3's http.server.CGIHTTPRequestHandler decodes
                # using the urllib.unquote default of UTF-8, amongst other
                # issues.
                elif (
                    software.startswith('simplehttp/')
                    and 'python/3' in software
                ):
                    v = v.encode('utf-8').decode('iso-8859-1')

                # For other servers, guess that they have written bytes to
                # the environ using stdio byte-oriented interfaces, ending up
                # with the system code page.
                else:
                    v = v.encode(enc, 'replace').decode('iso-8859-1')

            # Recover bytes from unicode environ, using surrogate escapes
            # where available (Python 3.1+).
            else:
                v = v.encode(enc, esc).decode('iso-8859-1')

        environ[k] = v
    return environ


class FileWrapper:
    """Wrapper to convert file-like objects to iterables"""

    def __init__(self, filelike, blksize=8192):
        self.filelike = filelike
        self.blksize = blksize
        if hasattr(filelike, 'close'):
            self.close = filelike.close

    def __getitem__(self, key):
        data = self.filelike.read(self.blksize)
        if data:
            return data
        raise IndexError

    def __iter__(self):
        return self

    def __next__(self):
        data = self.filelike.read(self.blksize)
        if data:
            return data
        raise StopIteration


def _formatparam(param, value=None, quote=1):
    """Convenience function to format and return a key=value pair.

    This will quote the value if needed or if quote is true.
    """
    tspecials = re.compile(r'[ \(\)<>@,;:\\"/\[\]\?=]')

    if value is not None and len(value) > 0:
        if quote or tspecials.search(value):
            value = value.replace('\\', '\\\\').replace('"', r'\"')
            return '%s="%s"' % (param, value)
        else:
            return '%s=%s' % (param, value)
    else:
        return param


class Headers:
    """Manage a collection of HTTP response headers"""

    def __init__(self, headers=None):
        headers = headers if headers is not None else []
        if type(headers) is not list:
            raise TypeError("Headers must be a list of name/value tuples")
        self._headers = headers
        if __debug__:
            for k, v in headers:
                self._convert_string_type(k)
                self._convert_string_type(v)

    def _convert_string_type(self, value):
        """Convert/check value type."""
        if type(value) is str:
            return value
        raise AssertionError("Header names/values must be"
            " of type str (got {0})".format(repr(value)))

    def __len__(self):
        """Return the total number of headers, including duplicates."""
        return len(self._headers)

    def __setitem__(self, name, val):
        """Set the value of a header."""
        del self[name]
        self._headers.append(
            (self._convert_string_type(name), self._convert_string_type(val)))

    def __delitem__(self,name):
        """Delete all occurrences of a header, if present.

        Does *not* raise an exception if the header is missing.
        """
        name = self._convert_string_type(name.lower())
        self._headers[:] = [kv for kv in self._headers if kv[0].lower() != name]

    def __getitem__(self,name):
        """Get the first header value for 'name'

        Return None if the header is missing instead of raising an exception.

        Note that if the header appeared multiple times, the first exactly which
        occurrence gets returned is undefined.  Use getall() to get all
        the values matching a header field name.
        """
        return self.get(name)

    def __contains__(self, name):
        """Return true if the message contains the header."""
        return self.get(name) is not None


    def get_all(self, name):
        """Return a list of all the values for the named field.

        These will be sorted in the order they appeared in the original header
        list or were added to this instance, and may contain duplicates.  Any
        fields deleted and re-inserted are always appended to the header list.
        If no fields exist with the given name, returns an empty list.
        """
        name = self._convert_string_type(name.lower())
        return [kv[1] for kv in self._headers if kv[0].lower()==name]


    def get(self,name,default=None):
        """Get the first header value for 'name', or return 'default'"""
        name = self._convert_string_type(name.lower())
        for k,v in self._headers:
            if k.lower()==name:
                return v
        return default


    def keys(self):
        """Return a list of all the header field names.

        These will be sorted in the order they appeared in the original header
        list, or were added to this instance, and may contain duplicates.
        Any fields deleted and re-inserted are always appended to the header
        list.
        """
        return [k for k, v in self._headers]

    def values(self):
        """Return a list of all header values.

        These will be sorted in the order they appeared in the original header
        list, or were added to this instance, and may contain duplicates.
        Any fields deleted and re-inserted are always appended to the header
        list.
        """
        return [v for k, v in self._headers]

    def items(self):
        """Get all the header fields and values.

        These will be sorted in the order they were in the original header
        list, or were added to this instance, and may contain duplicates.
        Any fields deleted and re-inserted are always appended to the header
        list.
        """
        return self._headers[:]

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self._headers)

    def __str__(self):
        """str() returns the formatted headers, complete with end line,
        suitable for direct HTTP transmission."""
        return '\r\n'.join(["%s: %s" % kv for kv in self._headers]+['',''])

    def __bytes__(self):
        return str(self).encode('iso-8859-1')

    def setdefault(self,name,value):
        """Return first matching header value for 'name', or 'value'

        If there is no header named 'name', add a new header with name 'name'
        and value 'value'."""
        result = self.get(name)
        if result is None:
            self._headers.append((self._convert_string_type(name),
                self._convert_string_type(value)))
            return value
        else:
            return result

    def add_header(self, _name, _value, **_params):
        """Extended header setting.

        _name is the header field to add.  keyword arguments can be used to set
        additional parameters for the header field, with underscores converted
        to dashes.  Normally the parameter will be added as key="value" unless
        value is None, in which case only the key will be added.

        Example:

        h.add_header('content-disposition', 'attachment', filename='bud.gif')

        Note that unlike the corresponding 'email.message' method, this does
        *not* handle '(charset, language, value)' tuples: all values must be
        strings or None.
        """
        parts = []
        if _value is not None:
            _value = self._convert_string_type(_value)
            parts.append(_value)
        for k, v in _params.items():
            k = self._convert_string_type(k)
            if v is None:
                parts.append(k.replace('_', '-'))
            else:
                v = self._convert_string_type(v)
                parts.append(_formatparam(k.replace('_', '-'), v))
        self._headers.append((self._convert_string_type(_name), "; ".join(parts)))


class BaseHandler:
    """Manage the invocation of a WSGI application"""

    # Configuration parameters; can override per-subclass or per-instance
    wsgi_version = (1,0)
    wsgi_multithread = True
    wsgi_multiprocess = True
    wsgi_run_once = False

    origin_server = True    # We are transmitting direct to client
    http_version  = "1.0"   # Version that should be used for response
    server_software = None  # String name of server software, if any

    # os_environ is used to supply configuration from the OS environment:
    # by default it's a copy of 'os.environ' as of import time, but you can
    # override this in e.g. your __init__ method.
    os_environ= read_environ()

    # Collaborator classes
    wsgi_file_wrapper = FileWrapper     # set to None to disable
    headers_class = Headers             # must be a Headers-like class

    # Error handling (also per-subclass or per-instance)
    traceback_limit = None  # Print entire traceback to self.get_stderr()
    error_status = "500 Internal Server Error"
    error_headers = [('Content-Type','text/plain')]
    error_body = b"A server error occurred.  Please contact the administrator."

    # State variables (don't mess with these)
    status = result = None
    headers_sent = False
    headers = None
    bytes_sent = 0

    def run(self, application):
        """Invoke the application"""
        # Note to self: don't move the close()!  Asynchronous servers shouldn't
        # call close() from finish_response(), so if you close() anywhere but
        # the double-error branch here, you'll break asynchronous servers by
        # prematurely closing.  Async servers must return from 'run()' without
        # closing if there might still be output to iterate over.
        try:
            self.setup_environ()
            self.result = application(self.environ, self.start_response)
            self.finish_response()
        except:
            try:
                self.handle_error()
            except:
                # If we get an error handling an error, just give up already!
                self.close()
                raise   # ...and let the actual server figure it out.


    def setup_environ(self):
        """Set up the environment for one request"""

        env = self.environ = self.os_environ.copy()
        self.add_cgi_vars()

        env['wsgi.input']        = self.get_stdin()
        env['wsgi.errors']       = self.get_stderr()
        env['wsgi.version']      = self.wsgi_version
        env['wsgi.run_once']     = self.wsgi_run_once
        env['wsgi.url_scheme']   = self.get_scheme()
        env['wsgi.multithread']  = self.wsgi_multithread
        env['wsgi.multiprocess'] = self.wsgi_multiprocess

        if self.wsgi_file_wrapper is not None:
            env['wsgi.file_wrapper'] = self.wsgi_file_wrapper

        if self.origin_server and self.server_software:
            env.setdefault('SERVER_SOFTWARE',self.server_software)


    def finish_response(self):
        """Send any iterable data, then close self and the iterable

        Subclasses intended for use in asynchronous servers will
        want to redefine this method, such that it sets up callbacks
        in the event loop to iterate over the data, and to call
        'self.close()' once the response is finished.
        """
        try:
            if not self.result_is_file() or not self.sendfile():
                for data in self.result:
                    self.write(data)
                self.finish_content()
        finally:
            self.close()


    def get_scheme(self):
        """Return the URL scheme being used"""
        return guess_scheme(self.environ)


    def set_content_length(self):
        """Compute Content-Length or switch to chunked encoding if possible"""
        try:
            blocks = len(self.result)
        except (TypeError,AttributeError,NotImplementedError):
            pass
        else:
            if blocks==1:
                self.headers['Content-Length'] = str(self.bytes_sent)
                return
        # XXX Try for chunked encoding if origin server and client is 1.1


    def cleanup_headers(self):
        """Make any necessary header changes or defaults

        Subclasses can extend this to add other defaults.
        """
        if 'Content-Length' not in self.headers:
            self.set_content_length()

    def start_response(self, status, headers,exc_info=None):
        """'start_response()' callable as specified by PEP 3333"""

        if exc_info:
            try:
                if self.headers_sent:
                    # Re-raise original exception if headers sent
                    raise exc_info[0](exc_info[1]).with_traceback(exc_info[2])
            finally:
                exc_info = None        # avoid dangling circular ref
        elif self.headers is not None:
            raise AssertionError("Headers already set!")

        self.status = status
        self.headers = self.headers_class(headers)
        status = self._convert_string_type(status, "Status")
        assert len(status)>=4,"Status must be at least 4 characters"
        assert status[:3].isdigit(), "Status message must begin w/3-digit code"
        assert status[3]==" ", "Status message must have a space after code"

        if __debug__:
            for name, val in headers:
                name = self._convert_string_type(name, "Header name")
                val = self._convert_string_type(val, "Header value")
                assert not is_hop_by_hop(name),"Hop-by-hop headers not allowed"

        return self.write

    def _convert_string_type(self, value, title):
        """Convert/check value type."""
        if type(value) is str:
            return value
        raise AssertionError(
            "{0} must be of type str (got {1})".format(title, repr(value))
        )

    def send_preamble(self):
        """Transmit version/status/date/server, via self._write()"""
        if self.origin_server:
            if self.client_is_modern():
                self._write(('HTTP/%s %s\r\n' % (self.http_version,self.status)).encode('iso-8859-1'))
                if 'Date' not in self.headers:
                    self._write(
                        ('Date: %s\r\n' % format_date_time(time.time())).encode('iso-8859-1')
                    )
                if self.server_software and 'Server' not in self.headers:
                    self._write(('Server: %s\r\n' % self.server_software).encode('iso-8859-1'))
        else:
            self._write(('Status: %s\r\n' % self.status).encode('iso-8859-1'))

    def write(self, data):
        """'write()' callable as specified by PEP 3333"""

        assert type(data) is bytes, \
            "write() argument must be a bytes instance"

        if not self.status:
            raise AssertionError("write() before start_response()")

        elif not self.headers_sent:
            # Before the first output, send the stored headers
            self.bytes_sent = len(data)    # make sure we know content-length
            self.send_headers()
        else:
            self.bytes_sent += len(data)

        # XXX check Content-Length and truncate if too many bytes written?
        self._write(data)
        self._flush()


    def sendfile(self):
        """Platform-specific file transmission

        Override this method in subclasses to support platform-specific
        file transmission.  It is only called if the application's
        return iterable ('self.result') is an instance of
        'self.wsgi_file_wrapper'.

        This method should return a true value if it was able to actually
        transmit the wrapped file-like object using a platform-specific
        approach.  It should return a false value if normal iteration
        should be used instead.  An exception can be raised to indicate
        that transmission was attempted, but failed.

        NOTE: this method should call 'self.send_headers()' if
        'self.headers_sent' is false and it is going to attempt direct
        transmission of the file.
        """
        return False   # No platform-specific transmission by default


    def finish_content(self):
        """Ensure headers and content have both been sent"""
        if not self.headers_sent:
            # Only zero Content-Length if not set by the application (so
            # that HEAD requests can be satisfied properly, see #3839)
            self.headers.setdefault('Content-Length', "0")
            self.send_headers()
        else:
            pass # XXX check if content-length was too short?

    def close(self):
        """Close the iterable (if needed) and reset all instance vars

        Subclasses may want to also drop the client connection.
        """
        try:
            if hasattr(self.result,'close'):
                self.result.close()
        finally:
            self.result = self.headers = self.status = self.environ = None
            self.bytes_sent = 0; self.headers_sent = False


    def send_headers(self):
        """Transmit headers to the client, via self._write()"""
        self.cleanup_headers()
        self.headers_sent = True
        if not self.origin_server or self.client_is_modern():
            self.send_preamble()
            self._write(bytes(self.headers))


    def result_is_file(self):
        """True if 'self.result' is an instance of 'self.wsgi_file_wrapper'"""
        wrapper = self.wsgi_file_wrapper
        return wrapper is not None and isinstance(self.result,wrapper)


    def client_is_modern(self):
        """True if client can accept status and headers"""
        return self.environ['SERVER_PROTOCOL'].upper() != 'HTTP/0.9'


    def log_exception(self,exc_info):
        """Log the 'exc_info' tuple in the server log

        Subclasses may override to retarget the output or change its format.
        """
        try:
            from traceback import print_exception
            stderr = self.get_stderr()
            print_exception(
                exc_info[0], exc_info[1], exc_info[2],
                self.traceback_limit, stderr
            )
            stderr.flush()
        finally:
            exc_info = None

    def handle_error(self):
        """Log current error, and send error output to client if possible"""
        self.log_exception(sys.exc_info())
        if not self.headers_sent:
            self.result = self.error_output(self.environ, self.start_response)
            self.finish_response()
        # XXX else: attempt advanced recovery techniques for HTML or text?

    def error_output(self, environ, start_response):
        """WSGI mini-app to create error output

        By default, this just uses the 'error_status', 'error_headers',
        and 'error_body' attributes to generate an output page.  It can
        be overridden in a subclass to dynamically generate diagnostics,
        choose an appropriate message for the user's preferred language, etc.

        Note, however, that it's not recommended from a security perspective to
        spit out diagnostics to any old user; ideally, you should have to do
        something special to enable diagnostic output, which is why we don't
        include any here!
        """
        start_response(self.error_status,self.error_headers[:],sys.exc_info())
        return [self.error_body]


    # Pure abstract methods; *must* be overridden in subclasses

    def _write(self,data):
        """Override in subclass to buffer data for send to client

        It's okay if this method actually transmits the data; BaseHandler
        just separates write and flush operations for greater efficiency
        when the underlying system actually has such a distinction.
        """
        raise NotImplementedError

    def _flush(self):
        """Override in subclass to force sending of recent '_write()' calls

        It's okay if this method is a no-op (i.e., if '_write()' actually
        sends the data.
        """
        raise NotImplementedError

    def get_stdin(self):
        """Override in subclass to return suitable 'wsgi.input'"""
        raise NotImplementedError

    def get_stderr(self):
        """Override in subclass to return suitable 'wsgi.errors'"""
        raise NotImplementedError

    def add_cgi_vars(self):
        """Override in subclass to insert CGI variables in 'self.environ'"""
        raise NotImplementedError


class SimpleHandler(BaseHandler):
    """Handler that's just initialized with streams, environment, etc.

    This handler subclass is intended for synchronous HTTP/1.0 origin servers,
    and handles sending the entire response output, given the correct inputs.

    Usage::

        handler = SimpleHandler(
            inp,out,err,env, multithread=False, multiprocess=True
        )
        handler.run(app)"""

    def __init__(self,stdin,stdout,stderr,environ,
        multithread=True, multiprocess=False
    ):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.base_env = environ
        self.wsgi_multithread = multithread
        self.wsgi_multiprocess = multiprocess

    def get_stdin(self):
        return self.stdin

    def get_stderr(self):
        return self.stderr

    def add_cgi_vars(self):
        self.environ.update(self.base_env)

    def _write(self,data):
        result = self.stdout.write(data)
        if result is None or result == len(data):
            return
        from warnings import warn
        warn("SimpleHandler.stdout.write() should not do partial writes",
            DeprecationWarning)
        while True:
            data = data[result:]
            if not data:
                break
            result = self.stdout.write(data)

    def _flush(self):
        self.stdout.flush()
        self._flush = self.stdout.flush
