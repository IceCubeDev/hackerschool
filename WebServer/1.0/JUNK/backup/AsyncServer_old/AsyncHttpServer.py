__author__ = 'Ivan Dortulov'

import socket
import select
import errno

from AsyncServer.EventDispatcher import *
from AsyncServer.ConnectionManager import *


##
# Class representing an asynchronous Http Server capable of handling GET and POST requests.
#
# The server uses an asynchronous approach to handle the incoming request. Each time a client connects, that client's
# socket gets associated with a Connection object.\n
# The Connection object uses the HttpRequestHandler class (each Connection object instantiates
# HttpRequestHandler) to process incoming request.\n
# Whenever a resource is request the HttpResponseHandler tells the
# TaskManager class to create a new Task for obtaining the file.
#
class AsyncHttpServer(EventDispatcher):

    ##
    # Default constructor.
    #
    def __init__(self, address, port):

        super(AsyncHttpServer, self).__init__()

        ## @var running
        # Is the server currently running.
        #
        self.running = False

        ## @var server_address
        # The host address of the server.
        #
        self.server_address = address
        ## @var server_port
        # The port on which the server is listening for incoming connections.
        #
        self.server_port = port

        ## @var connection_manager
        # Instance of the ConnectionManager class. Only one such instance exists per server.
        #
        self.connection_manager = ConnectionManager()

        ## @var address_family
        # The address family of the server
        #
        # Use this variable to change the type of the server's transport protocol to TCP or UDP.
        # Default is TCP (AF_INET).
        #
        self.address_family = socket.AF_INET
        ## @var socket_type
        # The type of the socket.
        #
        # Default is streaming socket (SOCK_STREAM)
        #
        self.socket_type = socket.SOCK_STREAM

        ## @var socket
        # The server socket used for listening.
        #
        self.socket = socket.socket(self.address_family, self.socket_type)

        self.add_event_listener(self.connection_manager, Event.NETWORK_CONNECT)
        self.add_event_listener(self.connection_manager, Event.NETWORK_DATA)
        self.add_event_listener(self.connection_manager, Event.NETWORK_DISCONNECT)

    ##
    # Bind the server socket.
    #
    def server_bind(self):

        self.socket.bind((self.server_address, self.server_port))

    ##
    # Activate the server.
    #
    # This method calls the server socket's listen() method.
    def server_activate(self):

        self.socket.listen(5)
        self.socket.setblocking(0)

        print("Listening on ", self.server_address, ":", self.server_port)
        self.running = True

    ##
    # Start the server.
    #
    # This method larches the server and makes it listen for incoming connections as well
    # as process incoming event.
    def server_forever(self):

        self.server_bind()
        self.server_activate()

        input_sockets = [self.socket]

        while self.running:
            (read, write, errors) = select.select(input_sockets, [], input_sockets)

            for sock in read:

                if sock is self.socket:
                    # A new connection has been established
                    (client, address) = self.socket.accept()

                    print("Client ", client.getpeername(), " has connected!")
                    input_sockets.append(client)
                    self.dispatch_event(Event(Event.NETWORK_CONNECT, client))

                else:
                    # We are receiving data
                    try:
                        data = sock.recv(256)

                    except socket.error as ex:

                        error = ex.args[0]

                        if error == errno.EAGAIN or error == errno.EWOULDBLOCK:
                            # No data available
                            continue
                        else:
                            print("Client has disconnected!")
                            # Signal the connection manager that a connection was terminated
                            self.dispatch_event(Event(Event.NETWORK_DISCONNECT, sock))

                            # Remove the socket from the list of inputs
                            input_sockets.remove(sock)
                            sock.close()

                    else:
                        if len(data) == 0:
                            print("Client ", sock.getpeername(), " has disconnected!")
                            # Normal connection close
                            # Signal the connection manager that a connection was terminated
                            self.dispatch_event(Event(Event.NETWORK_DISCONNECT, sock))

                            # Remove the socket from the list of inputs
                            input_sockets.remove(sock)
                            sock.close()

                        else:
                            self.dispatch_event(Event(Event.NETWORK_DATA, (sock, data)))

            for sock in errors:

                print("Client ", sock.getpeername(), " has disconnected!")
                sock.close()
                input_sockets.remove(sock)
                self.dispatch_event(Event(Event.NETWORK_DISCONNECT, sock))


theServer = AsyncHttpServer("127.0.0.1", 27015)
theServer.server_forever()