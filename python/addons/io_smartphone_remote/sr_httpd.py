# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function
import asyncio
import hashlib
import logging
import mimetypes
import os
import re
from datetime import datetime
from http.client import responses
from urllib.parse import unquote

logger = logging.getLogger(__name__)

def _get_response(**kwargs):
    """Get a template response

    Use kwargs to add things to the dictionary
    """
    if 'code' not in kwargs:
        kwargs['code'] = 200
    if 'headers' not in kwargs:
        kwargs['headers'] = dict()
    if 'version' not in kwargs:
        kwargs['version'] = 'HTTP/1.1'

    return dict(**kwargs)

class HttpProtocol(asyncio.Protocol):
    """HTTP/1.1 Protocol implementation

    Per connection made, one of these gets instantiated
    """

    def __init__(self, host, folder, event_loop=None, timeout=15):
        """Initialise a new instance.

        Arguments:
            host: the host to serve
            folder: the folder to serve files from
        """
        self.host = host
        self.folder = folder
        self.logger = logger.getChild('HttpProtocol {}'.format(id(self)))
        self.logger.debug('Instantiated HttpProtocol')
        self._loop = event_loop or asyncio.get_event_loop()
        self._timeout = timeout
        self._timeout_handle = None

    def _write_transport(self, string):
        """Convenience function to write to the transport"""
        if isinstance(string, str):  # we need to convert to bytes
            self.transport.write(string.encode('utf-8'))
        else:
            self.transport.write(string)

    def _write_response(self, response):
        """Write the response back to the client

        Arguments:
        response -- the dictionary containing the response.
        """
        status = '{} {} {}\r\n'.format(response['version'],
                                       response['code'],
                                       responses[response['code']])
        self.logger.debug("Responding status: '%s'", status.strip())
        self._write_transport(status)

        if 'body' in response and 'Content-Length' not in response['headers']:
            response['headers']['Content-Length'] = len(response['body'])

        response['headers']['Date'] = datetime.utcnow().strftime(
            "%a, %d %b %Y %H:%M:%S +0000")

        for (header, content) in response['headers'].items():
            self.logger.debug("Sending header: '%s: %s'", header, content)
            self._write_transport('{}: {}\r\n'.format(header, content))

        self._write_transport('\r\n')
        if 'body' in response:
            self._write_transport(response['body'])

    def connection_made(self, transport):
        """Called when the connection is made"""
        self.logger.info('Connection made at object %s', id(self))
        self.transport = transport
        self.keepalive = True

        if self._timeout:
            self.logger.debug('Registering timeout event')
            self._timout_handle = self._loop.call_later(
                self._timeout, self._handle_timeout)

    def connection_lost(self, exception):
        """Called when the connection is lost or closed.

        The argument is either an exception object or None. The latter means
        a regular EOF is received, or the connection was aborted or closed by
        this side of the connection.
        """
        if exception:
            self.logger.exception('Connection lost!')
        else:
            self.logger.info('Connection lost')

    def data_received(self, data):
        """Process received data from the socket

        Called when we receive data
        """
        self.logger.debug('Received data: %s', repr(data))

        try:
            request = self._parse_headers(data)
            self._handle_request(request)
        except InvalidRequestError as e:
            self._write_response(e.get_http_response())

        if not self.keepalive:
            if self._timeout_handle:
                self._timeout_handle.cancel()
            self.transport.close()

        if self._timeout and self._timeout_handle:
            self.logger.debug('Delaying timeout event')
            self._timeout_handle.cancel()
            self._timout_handle = self._loop.call_later(
                self._timeout, self._handle_timeout)

    def _parse_headers(self, data):
        self.logger.debug('Parsing headers')

        request_strings = list(map(lambda x: x.decode('utf-8'),
                                   data.split(b'\r\n')))

        request = dict()

        # Parse request method and HTTP version
        method_line = request_strings[0].split()

        # The first line has either 3 or 2 arguments
        if not (2 <= len(method_line) <= 3):
            self.logger.info('Got an invalid http header')
            self.keepalive = False  # We don't trust you
            raise InvalidRequestError(400, 'Bad request')
        # HTTP 0.9 isn't supported.
        if len(method_line) == 2:
            self.logger.info('Got a HTTP/0.9 request')
            self.keepalive = False  # HTTP/0.9 won't support persistence
            raise InvalidRequestError(505, "This server only supports HTTP/1.0"
                                           "and HTTP/1.1")
        else:
            request['version'] = method_line[2]

        # method
        request['method'] = method_line[0]
        # request URI
        request['target'] = method_line[1]

        # Parse the headers
        for line in request_strings[1:]:
            if line == '':  # an empty line signals the end of the headers
                break
            self.logger.debug("header: '%s'", line)
            header, body = line.split(': ', 1)
            request[header] = body

        self.logger.debug('request object: %s', request)
        return request

    def _get_request_uri(self, request):
        """Parse the request URI into something useful

        Server MUST accept full URIs (5.1.2)"""
        request_uri = request['target']
        if request_uri.startswith('/'):  # eg. GET /index.html
            return (request.get('Host', 'localhost').split(':')[0],
                    request_uri[1:])
        elif '://' in request_uri:  # eg. GET http://rded.nl
            locator = request_uri.split('://', 1)[1]
            host, path = locator.split('/', 1)
            return (host.split(':')[0], path)

    def _handle_request(self, request):
        """Process the headers and get the file"""

        # Check if this is a persistent connection.
        if request['version'] == 'HTTP/1.1':
            self.keepalive = not request.get('Connection') == 'close'
        elif request['version'] == 'HTTP/1.0':
            self.keepalive = request.get('Connection') == 'Keep-Alive'

        # Check if we're getting a sane request
        if request['method'] not in ('GET'):
            raise InvalidRequestError(501, 'Method not implemented')
        if request['version'] not in ('HTTP/1.0', 'HTTP/1.1'):
            raise InvalidRequestError(
                505, 'Version not supported. Supported versions are: {}, {}'
                .format('HTTP/1.0', 'HTTP/1.1'))

        host, location = self._get_request_uri(request)

        # We must ignore the Host header if a host is specified in GET
        if host is None:
            host = request.get('Host')

        # Check if this request is intended for this webserver
        if host is not None and not host == self.host:
            self.logger.info('Got a request for unknown host %s', host)
            raise InvalidRequestError(404, "We don't serve this host")

        filename = os.path.join(self.folder, unquote(location))
        self.logger.debug('trying to serve %s', filename)

        if os.path.isdir(filename):
            filename = os.path.join(filename, 'index.html')

        if not os.path.isfile(filename):
            raise InvalidRequestError(404, 'Not Found')

        # Start response with version
        response = _get_response(version=request['version'])

        # timeout negotiation
        match = re.match(r'timeout=(\d+)', request.get('Keep-Alive', ''))
        if match is not None:
            requested_timeout = int(match.group(1))
            if requested_timeout < self._timeout:
                self._timeout = requested_timeout

        # tell the client our timeout
        if self.keepalive:
            response['headers'][
                'Keep-Alive'] = 'timeout={}'.format(self._timeout)

        # Set Content-Type
        response['headers']['Content-Type'] = mimetypes.guess_type(
            filename)[0] or 'text/plain'

        # Generate E-tag
        sha1 = hashlib.sha1()
        with open(filename, 'rb') as fp:
            response['body'] = fp.read()
            sha1.update(response['body'])
        etag = sha1.hexdigest()

        # Create 304 response if if-none-match matches etag
        if request.get('If-None-Match') == '"{}"'.format(etag):
            # 304 responses shouldn't contain many headers we might already
            # have added.
            response = _get_response(code=304)

        response['headers']['Etag'] = '"{}"'.format(etag)

        self._write_response(response)

    def _handle_timeout(self):
        """Handle a timeout"""
        self.logger.info('Request timed out')
        self.transport.close()

class InvalidRequestError(Exception):
    """Raised for invalid requests. Contains the error code.

    This exception can be transformed to a http response.
    """

    def __init__(self, code, *args, **kwargs):
        """Configures a new InvalidRequestError

        Arguments:
            code -- the HTTP error code
        """
        super(InvalidRequestError, self).__init__(*args, **kwargs)
        self.code = code

    def get_http_response(self):
        """Get this exception as an HTTP response suitable for output"""
        return _get_response(
            code=self.code,
            body=str(self),
            headers={
                'Content-Type': 'text/plain'
            }
        )

def _start_server(bindaddr, port, hostname, folder):
    """Starts an asyncio server"""
    import asyncio

    #logging config
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('run method')

    loop = asyncio.get_event_loop()
    coroutine = loop.create_server(lambda: HttpProtocol(hostname, folder),
                                   bindaddr,
                                   port)
    server = loop.run_until_complete(coroutine)

    print('Starting server on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

#Test
if __name__ == '__main__':
    _start_server('0.0.0.0', 80,"192.168.0.17",'.')
