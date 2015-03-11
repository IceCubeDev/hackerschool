__author__ = 'Ivan Dortulov'

from HttpRequestHandler import *
import socket
import os
import logging
import errno
import select


class NonBlockingServer(object):

    CHUNK_SIZE = 1024
    MAX_HEADER_SIZE = 4098

    def __init__(self, address="localhost", port=27015, logfile=""):
        # Server settings
        self.server_address = address
        self.server_port = port
        self.server_variables = {"document_root": os.path.dirname(os.path.realpath(__file__))}

        # Create the server socket, bind it and listen
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setblocking(0)
        self.server_socket.bind((self.server_address, self.server_port))
        self.server_socket.listen(5)

        # List of socket states
        self.input_list = [self.server_socket]
        self.output_list = []

        # List of active connections
        self.connections = {}

        # Server is running
        self.running = True

        # Enable logging
        if len(logfile) > 0:
            logging.basicConfig(filename=logfile, level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.DEBUG)

        print("Listening on ", (self.server_address, self.server_port))

    # Called when a new connection is established
    def connection_open(self, client_socket, client_address):
        self.connections[client_socket] = HttpRequestHandler(self, client_address)

    # Close an open connection
    def connection_close(self, sock):
        if sock in self.input_list:
            self.input_list.remove(sock)
        if sock in self.output_list:
            self.output_list.remove(sock)

        if sock in self.connections.keys():
            conn = self.connections[sock]
            print("[DEBUG] connection_close: Closing " + str(conn.client_address))
            del self.connections[sock]
        else:
            print("[ERROR] connection_close: socket not in connections list!")

        try:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        except socket.error as ex:
            print("[ERROR] connection_close: socket.shutdown() " +
                  "or socket.close() has failed: " + str(ex))

    def check_for_input(self , read_list):
        for sock in read_list:
            if sock is self.server_socket:
                # A new connection is being established
                (client_socket, client_address) = self.server_socket.accept()

                # Switch to non-blocking mode and add socket to input list
                client_socket.setblocking(False)
                self.input_list.append(client_socket)

                # Create a handler to handle incoming requests
                self.connection_open(client_socket, client_address)
                print("[DEBUG] check_for_input: Connection from " +
                      str(client_address) + " accepted!")

            else:
                # Find the handler associated with this socket
                if sock in self.connections.keys():
                    connection = self.connections[sock]
                else:
                    print("[ERROR] check_for_input: Unable to handle input, " +
                          "connection not in connections list.")
                    self.connection_close(sock)
                    continue

                # Try to receive data
                try:
                    receive_data = sock.recv(NonBlockingServer.CHUNK_SIZE)
                except socket.error as ex:
                    print("[ERROR] check_for_input: "+ str(connection.client_address) +
                          " error has occurred while receiving data: " + str(ex))
                    self.connection_close(sock)
                else:
                    # We have received data successfully
                    if receive_data:
                        print("[DEBUG] check_for_input: " + str(connection.client_address) +
                              ": Received " + str(len(receive_data)) + " bytes of data: " +
                              receive_data.decode().replace("\r\n", "|"))

                        # Handle the received data
                        connection.handle_data(receive_data)

                        if sock not in self.output_list:
                            self.output_list.append(sock)
                    # Interpret empty result as a closed connection
                    else:
                        self.connection_close(sock)
                        print("[DEBUG] check_for_input: "+ str(connection.client_address) +
                              ": Disconnected.")

    def check_for_output(self, write_list):
        for sock in write_list:
            # Find the handler associated with this socket
            if sock in self.connections.keys():
                connection = self.connections[sock]
            else:
                print("[ERROR] check_for_output: Unable to handle output, " +
                      "connection not in connections list.")
                self.connection_close(sock)
                continue

            # If there is data to be sent
            if len(connection.output) > 0:
                # Send it
                try:
                    send = sock.send(connection.output[:NonBlockingServer.CHUNK_SIZE])
                except socket.error as ex:
                    error = ex.args[0]

                    if error != errno.EAGAIN or error != errno.EWOULDBLOCK:
                        print("[ERROR] check_for_output: "+ str(connection.client_address) +
                              ": Error sending data: " + str(ex.args[1]))
                        self.connection_close(sock)
                else:
                    data = connection.output[:send]
                    connection.output = connection.output[send:]

                    print("[DEBUG] check_for_output: "+ str(connection.client_address) +
                          ": Sent " + str(send) + " bytes of data" +
                          data.decode().replace("\r\n", "|"))
            elif connection.should_close:
                print("[DEBUG] check_for_output: "+ str(connection.client_address) +
                      ": Force close!")
                self.connection_close(sock)

    def check_for_errors(self, error_list):
        for sock in error_list:
            if sock in self.connections.keys():
                connection = self.connections[sock]
            else:
                print("[ERROR] check_for_errors: Found a socket which " +
                      "isn't associated with any connection.")
                self.connection_close(sock)
                continue

    def process_requests(self):
        for conn in self.connections:
            conn.handler.process_next_request()

    def serve_forever(self):
        while self.running:
            (read, write, error) = select.select(self.input_list, self.output_list, self.input_list)

            self.check_for_input(read)
            self.check_for_output(write)
            self.check_for_errors(error)

            for conn in self.connections.values():
                conn.process_next_request()
