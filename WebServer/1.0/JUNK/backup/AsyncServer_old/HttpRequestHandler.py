__author__ = 'Ivan Dortulov'

from AsyncServer.EventDispatcher import *
from AsyncServer.HttpResponse import *
from AsyncServer.TaskManager import *
import re
import queue
import os


class HttpRequest(object):

    def __init__(self):
        # Information about the requesting client's browser capabilities.
        self.browser = ""

        # The character set of the entity-body.
        self.contentEncoding = ""

        # The length, in bytes, of content sent by the client.
        self.contentLength = 0

        # MIME content type of the request
        self.contentType = ""

        # A collection of cookies sent by the client.
        self.cookies = []

        # Collection of form variables.
        self.form = {}

        # Collection of HTTP headers.
        self.headers = {}

        # The HTTP data transfer method (such as GET, POST, or HEAD) used by the client.
        self.method = ""

        # A collection of HTTP query string variables.
        # For example http://www.contoso.com/default.aspx?fullname=Ivan%20Dortulov has a query string fullname=Ivan Dortulov)
        self.queryStrings = {}

        # Information about the URL of the client's previous request that linked to the current URL.
        self.referrer = "";

        # Raw user agent string of the client browser.
        self.userAgent = "";

        # The IP host address of the remote client.
        self.userHostAddress = "";

        # The DNS name of the remote client.
        self.userHostName = "";

        # Sorted string array of client language preferences.
        self.userLanguages = []

        # The request uri
        self.requestUri = ""

        # Protocol version
        self.httpVersion = 1.0

        # Is the request ready to be processed
        self.ready = False

    # Returns a string that represents the current request.
    def dump(self):
        print("------> Request-line:")
        result = self.method + " "
        result += self.requestUri + "?"
        for key,value in self.queryStrings.items():
            result += key + "=" + value + "&"

        result = result[0:-1]
        result += " HTTP/" + str(self.httpVersion)
        print(result)

        print("------> Query String:")
        for key, value in self.queryStrings.items():
            print(key, "=", u''.join(value))

        print ("------> Headers:")
        for key, value in self.headers.items():
            print(key, ":", value)

    MAX_HEADER_LENGTH = 8 * 1024


class HttpRequestHandler(EventDispatcher):

    def __init__(self, connection):

        super(HttpRequestHandler, self).__init__()

        self.connection = connection
        self.state = HttpRequestHandler.PARSE_REQUEST
        self.current_request = None
        self.task_manager = TaskManager()
        self.request_queue = queue.Queue()
        self.processing = False

        self.add_event_listener(self.task_manager, Event.TASK_START)
        self.add_event_listener(self, Event.RECEIVED_REQUEST)

    def handle_event(self, event):

        _input = self.connection.input_buffer
        _output = self.connection.output_buffer

        if event.code == Event.NETWORK_DATA:

            _input.write(event.data)

            if _input.length() > HttpRequest.MAX_HEADER_LENGTH:
                _input.clear()

                _output.write(HttpResponse.generate(400, "The length of the <b>Request Headers</b> exceeds the server's maximum!"))
                self.dispatch_event(Event(Event.NETWORK_SEND, self.connection))
                print("Header overflow!")
                pass

            if _input.find(b"\r\n\r\n") >= 0 or _input.find(b"\n\n") >= 0:
                self.state = HttpRequestHandler.PARSE_REQUEST

                while(True):
                    line = _input.read_line()
                    request_line = HttpRequestHandler.find_request_line.match(line)

                    # Check for a request line
                    if request_line is not None:
                        self.current_request = HttpRequest()
                        self.current_request.method = request_line.group(1).decode().upper()
                        self.current_request.requestUri = request_line.group(2).decode()
                        self.current_request.httpVersion = float(request_line.group(4).decode())
                        print ("Received a ", self.current_request.method, " request!")
                        continue

                    # Find headers
                    if self.current_request is not None:
                        header = HttpRequestHandler.find_headers.match(line)

                        if header is not None:
                            name = header.group(1).decode().lower()
                            value = header.group(2).decode()
                            self.current_request.headers[name] = value
                            print("Http-Header: ", name, ": ", value)
                            continue


                    # Get content
                    if self.current_request is not None:
                        if len(line) == 0:
                            # This is to be handled elsewhere :D
                            if self.current_request.method == "POST":
                                self.state = HttpRequestHandler.RECEIVE_CONTENT
                                # Start a task to handle the incoming content
                                break
                            elif self.current_request.method == "GET":
                                #self.request_queue.put(self.current_request)
                                print("Request added to request queue!")

                                """
                                _output.write(HttpResponse.generate(200, "Hey there!"))
                                self.dispatch_event(Event(Event.NETWORK_SEND, self.connection))"""
                                self.request_queue.put(self.current_request)
                                self.dispatch_event(Event(Event.RECEIVED_REQUEST, ""))
                                self.current_request = None
                                break

                        else:
                            # If we got here, either we are receiving a request, or
                            # we haven't received the entire request
                            _input.write(line)
                            break

        elif event.code == Event.RECEIVED_REQUEST:

            if self.processing:
                pass

            try:
                request = self.request_queue.get(False)

            except queue.Empty:
                pass

            else:

                if os.path.isdir(request.requestUri):

                    """if os.path.isfile(request.request_uri):

                        self.processing = True
                        response = HttpResponse()
                        size = os.path.getsize(request.request_uri)
                        response.headers["Content-Length"] = str(size)
                        _output.write(response.raw())
                        self.dispatch_event(Event(Event.NETWORK_SEND, self.connection))
                    else:"""
                    response = HttpResponse()
                    response.statusCode = 404
                    response.reasonPhase = "Not Found"

                    data = b"<html>\n<title>404 - Not Found</title>\n<body>\n<h1> 404 - Not Found</h1>\n"
                    data += b"The resource you requested was not found on this server!"
                    response.headers["Content-Length"] = str(len(data))

                    _output.write(response.raw() + data)
                    self.dispatch_event(Event(Event.NETWORK_SEND, self.connection))
                    self.dispatch_event(Event(Event.RECEIVED_REQUEST, ""))



    # Regular expressions
    find_request_line = re.compile(b"(^GET)\s(.*)(?=\sHTTP)(\sHTTP\/)([1]\.[0-1])")
    find_headers = re.compile(b"(.*):\s(.*)")

    (PARSE_REQUEST, RECEIVE_CONTENT) = range(0, 2)