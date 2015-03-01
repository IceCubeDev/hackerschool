__author__ = 'Ivan Dortulov'

import socket
import os
import select

from Log import *
from RequestHandler import *


class WebServer(object):

    CHUNK_SIZE = 512

    def __init__(self, server_address="localhost", server_port=80):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (server_address, server_port)
        self.server_variables = {"document_root":
                                 os.path.dirname(os.path.realpath(__file__))}

        self.running = False
        self.socket_list = [self.server_socket]
        self.connections = {}

    def listen(self):
        Log.d("WebServer", "Listening on " + str(self.server_address))

        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setblocking(0)
        self.server_socket.bind(self.server_address)
        self.server_socket.listen(5)

    def serve_forever(self):
        self.listen()
        self.running = True

        while self.running:
            (read, write, error) = select.select(self.socket_list, self.socket_list, self.socket_list)

            for sock in read:
                if sock is self.server_socket:
                    self.open_connection()
                else:
                    try:
                        receive_data = sock.recv(WebServer.CHUNK_SIZE)
                    except socket.error as ex:
                        Log.d("WebServer", "recv - " + ex.args[1])
                        self.close_connection(sock)
                    else:
                        self.handle_recv_data(sock, receive_data)

            for sock in write:
                self.handle_send_data(sock)

            for (sock, handler) in self.connections.items():
                handler.process_next_request()

    def open_connection(self):
        (client_socket, client_address) = self.server_socket.accept()

        client_socket.setblocking(False)
        self.socket_list.append(client_socket)
        self.connections[client_socket] = RequestHandler(self, str(client_address))
        Log.d("WebServer", "open_connection: New connection from " + str(client_address))


    def handle_recv_data(self, sock, data):
        if sock not in self.connections.keys():
            Log.w("WebServer", "handle_recv_data: connection not found")
            pass

        connection = self.connections[sock]
        Log.d("WebServer", "handle_recv_data: received " + str(len(data)) + " bytes of data from " + connection.address)
        Log.d("WebServer", data)

        if not data:
            self.close_connection(sock)
        else:
            self.connections[sock].process_data(data)

    def close_connection(self, sock):
        if sock in self.socket_list:
            self.socket_list.remove(sock)

        if sock in self.connections.keys():
            connection = self.connections[sock]
            Log.d("WebServer", "close_connection: Closing " + connection.address)
            del self.connections[sock]

        try:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        except socket.error as ex:
            Log.w("WebServer", "close_connection: Unable to close socket properly. " + str(ex.args[1]))

    def handle_send_data(self, sock):
        if sock not in self.connections.keys():
            Log.w("WebServer", "handle_send_data: Connection not in list!")
        else:
            connection = self.connections[sock]
            if len(connection.output) > 0:
                try:
                    sent = sock.send(connection.output[:WebServer.CHUNK_SIZE])
                except socket.error as ex:
                    Log.w("WebServer", "send: Error while sending data: " + str(ex.args[1]))
                    self.close_connection(sock)
                else:
                    data = connection.output[:sent]
                    connection.output = connection.output[sent:]

                    Log.d("WebServer", "handle_send_data: Sent " + str(sent) + " bytes to " + connection.address)
                    Log.d("WebServer", data)
            elif connection.should_close:
                Log.d("WebServer", "handle_send_data: All data processed. Closing ...")
                self.close_connection(sock)