__author__ = 'Ivan Dortulov'

from web.ServerBase import *
from web.RequestHandler import *
from web.async.AsyncRequestHandler import *
from web.async.EventDispatcher import *
from web.async.Connection import *

import socket
import errno


class AsyncServer(BaseServer, EventDispatcher):

    def __init__(self, address, port, handler=AsyncRequestHandler):
        AsyncServer.address_family = socket.AF_INET
        AsyncServer.socket_type = socket.SOCK_STREAM

        super(AsyncServer, self).__init__(address, port, handler)

        self.socket.setblocking(0)

        self.handler = self.RequestHandlerClass()
        self.handler.server = self
        self.add_event_listener(self.handler, Event.NETWORK_CONNECT)
        self.add_event_listener(self.handler, Event.NETWORK_DATA)
        self.add_event_listener(self.handler, Event.NETWORK_DISCONNECT)
        self.add_event_listener(self.handler, Event.NETWORK_SEND)

    def serve_forever(self):
        print ("Listening on ", self.server_address, ":", self.server_port)

        input_sockets = [self.socket]
        output_sockets = []

        while input_sockets:
            (read, write, errors) = select.select(input_sockets, output_sockets, input_sockets)

            for sock in read:

                if sock is self.socket:
                    # A new connection has been established
                    (client, address) = self.socket.accept()

                    print("Client ", client.getpeername(), " has connected!")
                    input_sockets.append(client)
                    output_sockets.append(client)

                    self.dispatch_event(Event(Event.NETWORK_CONNECT, client))

                else:
                    # We are receiving data
                    try:
                        data = sock.recv(128)

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

                            if sock in output_sockets:
                                output_sockets.remove(sock)

                    else:

                        if len(data) == 0:
                            print("Client ", sock.getpeername(), " has disconnected!")

                            # Normal connection close
                            # Signal the connection manager that a connection was terminated
                            self.dispatch_event(Event(Event.NETWORK_DISCONNECT, sock))

                            # Remove the socket from the list of inputs
                            input_sockets.remove(sock)

                            if sock in output_sockets:
                                output_sockets.remove(sock)

                        else:
                            self.dispatch_event(Event(Event.NETWORK_DATA, (sock, data)))

            for sock in write:
                self.dispatch_event(Event(Event.NETWORK_SEND, sock))

            for sock in errors:
                print("Client ", sock.getpeername(), " has disconnected!")

                self.dispatch_event(Event(Event.NETWORK_DISCONNECT, sock))

                input_sockets.remove(sock)
                if sock in output_sockets:
                    output_sockets.remove(sock)