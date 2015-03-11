__author__ = 'Ivan Dortulov'

from web.RequestHandler import *
from web.HttpRequest import *
from web.HttpResponse import *
import select
import queue
import errno
import socket
import os


class ThreadedRequestHandler(RequestHandler):

    def __init__(self):

        super(ThreadedRequestHandler, self).__init__()

        self.parent = None
        self.input = b""
        self.output = b""
        self.current_request = None
        self.request_queue = queue.Queue()
        self.rfile = None
        self.wfile = None

    def setup(self):
        self.request.setblocking(False)

    def handle(self):
        (read, write, error) = select.select([self.request], [self.request], [self.request])

        for s in read:
            # Handle data received
            try:
                data = s.recv(128)

            except  socket.error as ex:
                error = ex.args[0]

                if error == errno.EAGAIN or error == errno.EWOULDBLOCK:
                    # No data available
                    print ("Received 0 bytes")
                    continue
                else:
                    self.parent.should_close = True
            else:
                if len(data) == 0:
                    self.parent.should_close = True
                else:
                    self.input += data

                    print("Received: ", data)

                    clrf = self.input.find(b"\r\n\r\n")

                    # Check if we have received end of Http-Headers
                    if clrf >= 0:
                        print ("Request detected!")
                        # Get the request as a string
                        request_string = self.input[:clrf + 4]

                        # Parse the request string and create a HttpRequest object
                        request = HttpRequest(request_string.decode())

                        if self.current_request is None:
                            # Set the current request
                            self.current_request = request

                            #response = HttpResponse(404, "The requested resource could not be located on this server.")
                            #print ("Response: ", response.response)
                            #self.output += response.response
                            #self.output += b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(request_string)).encode() + b"\r\n"
                            #self.output += b"Content-Type: text/plain; charset=utf-8\r\nConnection: keep-alive\r\n" + b"\r\n" + request_string
                            self.input = self.input[clrf + 4:]
                        else:
                            self.request_queue.put(request)
                    else:
                        if len(self.input) > HttpRequest.MAX_HEADER_LENGTH:
                            response = HttpResponse(400, "You have sent a request which exceeds the maximum header length supported by the server. ")

        self.handle_current_request()

        if len(self.output) > 0:
            data = self.output[0:256]
            self.output = self.output[256:]
            print ("Returning: ", data)

            try:
                self.request.sendall(data)
            except IOError:
                pass


    def finish(self):
        print ("Closing connection ", self.request.getpeername())

        try:
            self.request.close()
        except socket.error:
            pass

    def handle_current_request(self):
        if self.current_request is not None:
            if len(self.current_request.request_uri) > 1024:
                response = HttpResponse(400, "You have sent a request which has a query string which exceeds the maximum length supported by the server.")
                self.current_request.processed = True
                self.output += response.response
            else:
                #response = HttpResponse(404, "The requested resource could not be located on this server.")
                #self.current_request.processed = True
                #self.output += response.response

                if self.current_request.method == "GET":
                    print ("Handling GET request!")
                    # Get the requested resource
                    file_path = self.server.document_root
                    file_path = file_path[:file_path.rfind("/")] + "/public_html" + self.current_request.request_uri
                    print (file_path)
                    #print (file_path)

                    if self.rfile is None:
                        if os.path.isfile(file_path):
                            try:
                                print("Opening file.")
                                self.rfile = open(file_path, "rb")
                            except IOError:
                                print("Error opening file!")
                                response = HttpResponse(403, "You do not have sufficient privileges to read the requested resource.")
                                self.current_request.processed = True
                            else:
                                print("File found, sending...")
                                name, ext = os.path.splitext(file_path)
                                size = os.path.getsize(file_path)

                                #response = HttpResponse(200, (size, "image/" + ext[1:]))
                                response = HttpResponse(200, (size, ext[1:]))
                                self.output += response.response
                        else:
                            if os.path.isdir(file_path):
                                listing = self.list_directory(file_path)

                                response = HttpResponse(200, (len(listing), "txt"))
                                self.output += response.response

                                self.output += listing.encode()
                                self.current_request.processed = True
                            else:
                                print ("File not found!")
                                response = HttpResponse(404, "The resource <b>" + file_path + "</b> could not be located by the server.")
                                self.output += response.response
                                self.current_request.processed = True
                    else:
                        print("Chunk")
                        data = self.rfile.read(128)
                        if not data:
                            self.current_request.processed = True
                            self.rfile.close()
                            self.rfile = None
                        else:
                            self.output += data

            if self.current_request.processed == True:
                try:
                    next = self.request_queue.get(False)
                except queue.Empty:
                    self.current_request = None
                else:
                    self.current_request = next

    def list_directory(self, directory):
        listing = ""
        for root, dirs, files in os.walk(directory):
            level = root.replace(directory, '').count(os.sep)
            indent = ' ' * 4 * (level)
            listing += '{}{}/'.format(indent, os.path.basename(root)) + "\n"
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                listing += '{}{}'.format(subindent, f) + "\n"

        return listing