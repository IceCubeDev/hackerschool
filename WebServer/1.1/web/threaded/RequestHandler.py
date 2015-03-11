__author__ = 'Ivan Dortulov'

from web.HttpRequest import *
import os


class RequestHandler(object):

    def __init__(self, server):
        self.server = server
        self.input = b""
        self.output = b""
        self.should_close = False
        self.file = None
        self.request_queue = []
        self.current_request = None

    def receive_data(self, data):
        #print ("Handling data")
        self.input += data

        clrf = self.input.find(b"\r\n\r\n")
        if clrf >= 0:
            data = self.input[:clrf+4]
            self.input = self.input[clrf+4:]

            self.request_queue.append(HttpRequest(data.decode()))
            print("Request detected!")

            #self.output += b"HTTP/1.0 200 OK\r\n"
            #self.output += b"Content-Type: text/plain\r\n"
            #self.output += b"Content-Length: " + str(len(data)).encode() +  b"\r\n\r\n"
            #self.output += data

            #self.should_close = True

    def handle_next(self):
        if self.current_request is None:
            if len(self.request_queue) > 0:
                print("Setting new request!")
                self.current_request = self.request_queue.pop()
                #self.current_request.dump()

                if self.current_request.method == "GET":
                    file_path = self.server.document_root + self.current_request.request_uri

                    print("Requested resource: ", file_path)

                    if os.path.isfile(file_path):
                        try:
                            print("Opening requested resource!")
                            self.file = open(file_path, "rb")
                        except IOError as error:
                            #TODO: respond appropriately
                            print("Error opening file!")
                            self.file = None
                            pass
                        else:
                            self.current_request.remaining = os.path.getsize(file_path)
                            print("File size: ", self.current_request.remaining)
                            self.output += b"HTTP/1.0 200 OK\r\nContent-type: text/html\r\nContent-Length:"
                            self.output += str(self.current_request.remaining).encode() + b"\r\n\r\n"
                    else:
                        message = b"<html><body><h1> 404 - NOT FOUND</h1></body></html>"
                        self.output += b"HTTP/1.0 200 OK\r\nContent-Length:" + str(len(message)).encode()
                        self.output += b"\r\nContent-Type: text/html\r\n\r\n" + message

                        del self.current_request
                        self.current_request = None
                        self.should_close = True
            #else:
            #    self.should_close = True
        else:
            if self.current_request.remaining > 0:
                try:
                    data = self.file.read(128)
                except IOError as error:
                    print ("Something went wrong!", error)
                    #TODO: generate appropriate response (internal server error)
                    self.should_close = True
                    self.file.close()
                    self.file = None
                else:
                    print("Read ", data, " from the file")
                    self.output += data
                    self.current_request.remaining -= len(data)
            else:
                print("Reached end of file!")
                self.file.close()
                self.file = None
                self.should_close = True

                del self.current_request
                self.current_request = None