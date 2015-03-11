__author__ = 'Ivan Dortulov'

import queue
import re
import os

class HttpRequest(object):

    def __init__(self, request_string):
        self.remaining = 0
        self.processing = False
        
        idx = request_string.find("\r\n")
        self.request_line = request_string[:idx].split()
        request_string = request_string[idx + 2:]

        self.headers = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", request_string))

        self.request_method = self.request_line[0]
        self.request_uri = self.request_line[1]
        self.request_version = self.request_line[2]

class HttpRequestHandler(object):

    def __init__(self, server, client_address):

        # Server references to get access to server variables
        self.server = server

        self.client_address = client_address

        # Input buffer
        self.input = b""
        # Output buffer
        self.output = b""
        # Should this connection be closed
        self.should_close = False

        # The request we are currently processing
        self.current_request = None
        # List of pending requests
        self.request_queue = queue.Queue()

        # Handle to the requested resource
        self.file = None

    def handle_data(self, data):
        self.input += data

        # Check if a request has arrived
        idx = self.input.find(b"\r\n\r\n")

        if idx >= 0:
            request_string = self.input[:idx + 4].decode()
            self.input = self.input[idx + 4:]

            # Parse the request
            request = HttpRequest(request_string)

            # Add it to the request queue
            self.request_queue.put(request)

            #self.output += b"HTTP/1.1 200 OK\r\n" \
            #               b"Content-Length:" + str(len(data)).encode() + b"\r\n"
            #self.output += b"Content-Type: text/plain\r\n\r\n" + data
            #self.should_close = True
    
    def process_next_request(self):
        if self.current_request is not None:
            if self.current_request.processing:
                if self.current_request.remaining <= 0:
                    print("[DEBUG] process_next_request: " + str(self.client_address) +
                          ": Request processed: " + str(self.current_request.request_line))
                    del self.current_request
                    self.current_request = None
                    self.should_close = True

                    if self.file is not None:
                        self.file.close()
                        self.file = None
                else:
                    if self.current_request.request_method == "GET":
                        try:
                            read_chunk = self.file.read(self.server.CHUNK_SIZE)
                        except IOError as ex:
                            print("[DEBUG] process_next_request: " + str(self.client_address) +
                                  ": Error processing request: " + str(ex.args[1]))
                            self.current_request.remaining = 0
                            del self.current_request
                            self.current_request = None
                        else:
                            print("[DEBUG] process_next_request: " + str(self.client_address) +
                                  ": Read " + str(len(read_chunk)) + " bytes from " +
                                  self.current_request.request_uri)

                            # Add what we read from the file to the output
                            self.output += read_chunk
                            self.current_request.remaining -= len(read_chunk)
        else:
            if not self.request_queue.empty():
                self.current_request = self.request_queue.get()
                self.current_request.processing = True

                # Find the request resource
                file_path = self.server.server_variables["document_root"] + "/public_html" + \
                            self.current_request.request_uri

                print("[DEBUG] process_next_request: " + str(self.client_address) +
                      ": Requested file '" + str(file_path) + "'")

                if self.current_request.request_method == "GET":
                    if os.path.isfile(file_path):
                        try:
                            self.file = open(file_path, "rb")
                        except IOError as ex:
                            # TODO: Return appropriate response
                            print("[ERROR] process_next_request: " + str(self.client_address) +
                                  ": Error opening file '" + str(file_path) + "': " + ex.args[1])
                        else:
                            (file_name, file_ext) = os.path.splitext(os.path.basename(file_path))

                            # Get the size of the file
                            # TODO: add script support for file size
                            file_size = os.path.getsize(file_path)

                            print("[DEBUG] process_next_request: " + str(self.client_address) +
                                  ": Requested file '" + str(file_path) + "' was opened successfully! (" +
                                  str(file_size) + " bytes)")

                            # TODO: Add appropriate content-type based on file extension
                            response = HttpRequestHandler.generate_response(200,
                                        self.current_request.request_version, {"Content-Length": file_size,
                                                                               "Content-Type": "text/plain"}).encode()

                            print("[DEBUG] process_next_request: " + str(self.client_address) +
                                  ": Generated response: ", response)

                            self.current_request.remaining = file_size
                            self.current_request.processing = True

    @staticmethod
    def generate_response(code, version, headers):
        response = ""

        if code == 200:
            response += "HTTP/" + str(version) + " " + str(code) + " OK\r\n"
            for (key, value) in headers.items():
                response += str(key) + ": " + str(value) + "\r\n"
            response += "\r\n"

        return response

