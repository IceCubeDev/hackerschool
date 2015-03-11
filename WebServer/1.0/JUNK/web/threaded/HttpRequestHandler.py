__author__ = 'Ivan Dortulov'

from web.HttpRequest import HttpRequest
from web.HttpResponse import HttpResponse

import queue
import os


class HttpRequestHandler(object):

    REQUEST_READ = 0
    REQUEST_WRITE = 1
    UNSUPPORTED = 2
    CHUNK_SIZE = 256

    def __init__(self, request, parent):
        self.parent = parent
        self.server = parent.server
        self.input = b""
        self.output = b""
        self.should_close = False
        self.socket = request
        self.request_queue = queue.Queue()
        self.current_request = None
        self.file = None
        print("[", self.parent.name, "] Request handler created for ", self.socket.getpeername())

    def process_current(self):
        # If there is a request pending
        if self.current_request is not None:
            # And it has not yet been processed
            if not self.current_request.processed:
                # Get the type of the request
                if self.request_get_type(self.current_request) == HttpRequestHandler.REQUEST_READ:
                    # If there is still work to be done
                    if self.current_request.remaining > 0:
                        # Read a chunk from the file and add it to the output
                        try:
                            print("[", self.parent.name, "] Reading chunk from file for client ", self.socket.getpeername(), "...")
                            chunk = self.file.read(HttpRequestHandler.CHUNK_SIZE)
                        except IOError as ex:
                            #TODO: Handle file read error
                            print("[", self.parent.name, "] Error while reading: ", ex)
                            self.should_close = True
                        else:
                            self.output += chunk
                            self.current_request.remaining -= len(chunk)
                            print("[", self.parent.name, "] Read ", len(chunk), " bytes from the file for ", self.socket.getpeername())
                    # Nothing left to be done, so mark the request as processed
                    else:
                        print("[", self.parent.name, "] Request by ", self.socket.getpeername(), " remaining 0!")
                        self.current_request.processed = True
                        if self.file is not None:
                            print("[", self.parent.name, "] Closing file requested by ", self.socket.getpeername())
                            self.file.close()
                            self.file = None
            else:
                print("[", self.parent.name, "] Request by ", self.socket.getpeername(), " was processed!")
                del self.current_request
                self.current_request = None
                self.should_close = True
        else:
            # Set as current request if no other request are pending
            if not self.request_queue.empty():
                self.init_request(self.request_queue.get(False))
                self.should_close = False
                print("[", self.parent.name, "] Getting next request: ", self.current_request.method, self.current_request.request_uri)


    def handle_data(self, data):
        self.input += data

        print("[", self.parent.name, "] Received ", len(data), " bytes from ", self.socket.getpeername())

        idx = self.input.find(b"\r\n\r\n")

        if idx >= 0:
            # Detected a new request
            request_string = self.input[:idx + 4]
            self.input = self.input[idx+4:]

            # Parse the request
            request = HttpRequest(request_string.decode())

            print("[", self.parent.name, "] Request detected: ", request.method, request.request_uri)

            # Add request to request queue
            self.request_queue.put(request)

    def init_request(self, request):
        self.current_request = request

        # If the file is already opened, close it
        if self.file is not None:
            self.file.close()
            self.file = None

        # This is a get request
        if self.current_request.method == "GET":
            # Get the path to the request file
            if self.current_request.request_uri == "/":
                file_path = self.server.document_root
            else:
                file_path = self.server.document_root + self.current_request.request_uri

            print("[", self.parent.name, "]", file_path, " requested by ", self.socket.getpeername())

            # Check if the file exists
            if os.path.isfile(file_path):
                # Open the file
                try:
                    self.file = open(file_path, "rb")
                except IOError as ex:
                    #TODO: Reply with internal server error
                    print("[", self.parent.name, "]: Erro ocurred while opening file: ", ex)
                    pass
                else:
                    # Get the file size
                    self.current_request.remaining = os.path.getsize(file_path)
                    self.current_request.processed = False
                    self.should_close = False

                    # find out the file extension
                    file_name, file_extension = os.path.splitext(file_path)

                    print("[", self.parent.name, "] File ", file_path, " found! Request by ", self.socket.getpeername())

                    # generate a response
                    response = HttpResponse(200, (self.current_request.remaining, file_extension[1:]))
                    self.output += response.response
                    del response

            elif os.path.isdir(file_path):
                listing = self.list_directory(file_path)

                response = HttpResponse(200, (len(listing), "txt"))
                self.output += response.response

                print("[", self.parent.name, "] Listing directory! Request by ", self.socket.getpeername())

                self.output += listing.encode()
                self.current_request.remaining = 0
                self.current_request.processed = True
                del response
            else:
                print("[", self.parent.name, "] File ", file_path, " NOT found! Request by ", self.socket.getpeername())
                self.current_request.remaining = 0
                self.current_request.processed = True

                response = HttpResponse(404, "")
                self.output += response.response
                del response

    def request_get_type(self, request):
        if request.method == "GET":
            return HttpRequestHandler.REQUEST_READ
        elif request.method == "POST":
            return HttpRequestHandler.REQUEST_WRITE
        else:
            return HttpRequestHandler.UNSUPPORTED

    def list_directory(self, directory):
        listing = ""
        x

        return listing