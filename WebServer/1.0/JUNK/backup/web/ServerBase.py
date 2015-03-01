__author__ = 'Ivan Dortulov'

import socket
import select
import sys
import os

from web.RequestHandler import *


##
# This is a base class for all Server objects in this package.
#
# The BaseServer class defines the basic interface for Server objects, but
# does not implement most of the methods. This should be done in the subclasses.
#
class BaseServer(object):

    ##
    # The family of protocols to which the server’s socket belongs.
    #
    # Common examples are socket.AF_INET and socket.AF_UNIX.
    #
    address_family = socket.AF_INET

    ##
    # The type of socket used by the server.
    #
    # Common examples ares socket.SOCK_STREAM and socket.SOCK_DGRAM.
    #
    socket_type = socket.SOCK_STREAM

    def __init__(self, address, port, handler=RequestHandler):

        super(BaseServer, self).__init__()

        self.RequestHandlerClass = handler
        self.server_address = address
        self.server_port = port
        self.socket = None
        self.inputs = []
        self.document_root = os.path.dirname(os.path.realpath(__file__))

        self.server_bind()
        self.server_activate()

    ##
    # Process a single request. This function calls the following methods in order: get_request(),
    # verify_request(), and process_request(). If the user-provided handle() method of the handler
    # class raises an exception, the server’s handle_error() method will be called.
    #
    def handle_request(self):
        (request, client_address) = self.get_request()
        self.verify_request(request, client_address)
        self.process_request(request, client_address)

    ##
    # Actually processes the request by instantiating RequestHandlerClass and calling its handle() method.
    #
    def finish_request(self, request, client_address):
        if self.RequestHandlerClass is not None:
            print("Instantiating the RequestHandlerClass.")
            handler = self.RequestHandlerClass()

            handler.server = self
            handler.request = request
            handler.client_address = client_address

            handler.setup()
            handler.handle()
            handler.finish()

            if handler.should_close:
                request.close()

        return None

    ##
    # Must accept a request from the socket, and return a 2-tuple containing the new socket object to be used
    # to communicate with the client, and the client’s address.
    def get_request(self):
        (request, client_address) = self.socket.accept()
        print("Accepting new request from ", request.getpeername())
        return (request, client_address)

    ##
    # Must return a Boolean value; if the value is True, the request will be processed, and if it’s False,
    # the request will be denied. This function can be overridden to implement access controls for a server.
    # The default implementation always returns True.
    #
    def verify_request(self, request, client_address):
        print ("Request is valid!")
        return True

    ##
    # Calls finish_request() to create an instance of the RequestHandlerClass. If desired, this function can create
    # a new process or thread to handle the request.
    #
    def process_request(self, request, client_address):
        print("Processing request!")
        self.finish_request(request, client_address)

    ##
    # Handle requests until an explicit shutdown() request.
    #
    def serve_forever(self):
        print ("Listening on ", self.server_address, ":", self.server_port)

        while self.inputs:
            # Check for incoming connections
            (read, write, error) = select.select(self.inputs, [], self.inputs)

            for s in read:
                if s is self.socket:
                    # A new request (connection) has been made to the server.
                    self.handle_request()

    ##
    # Tell the serve_forever() loop to stop and wait until it does.
    #
    def shutdown(self):
        print ("Shutting down the server ....")
        if self.socket in self.inputs:
            self.inputs.remove(self.socket)
            self.socket.close()

    ##
    # This function is called if the RequestHandlerClass‘s handle() method raises an exception.
    # The default action is to print the traceback to standard output and continue handling further requests.
    def handle_error(self, request, client_address):
        pass

    ##
    # Called by the server’s constructor to bind the socket to the desired address.
    #
    # May be overridden.
    #
    def server_bind(self):
        self.socket = socket.socket(BaseServer.address_family, BaseServer.socket_type)

        if self.socket is not None:
            self.socket.bind((self.server_address, self.server_port))

    ##
    # Called by the server’s constructor to activate the server.
    #
    # The default behavior just listen()s to the server’s socket. May be overridden.
    #
    def server_activate(self):
        if self.socket is not None:
            self.socket.listen(5)
            self.inputs.append(self.socket)