__author__ = 'Ivan Dortulov'

from RequestParser import *
import socket
import select
import os
import errno


class NonBlockingServer(object):
    # Maximum size of the html header
    MAX_HEADER_SIZE = 4096

    def __init__(self, address="localhost", port=27015):
        # Server address, port and size of the data chunks to be received and send by the server
        self.server_address = address
        self.server_port = port
        self.chunk_size = 1024

        # Create the server socket, bind it and listen
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setblocking(0)
        self.server_socket.bind((self.server_address, self.server_port))
        self.server_socket.listen(10)
        print("Listening on ", (self.server_address, self.server_port))

        # List of sockets having input
        self.input_list = [self.server_socket]
        # List of sockets having output
        self.output_list = []
        # List of sockets in error state
        self.error_list = [self.server_socket]

        # List of active connections
        self.connections = {}

        # Server is running
        self.running = True

        # List of server variables like document root, server name, port and etc...
        self.server_variables = {"document_root" : os.path.dirname(os.path.realpath(__file__))}

        self.log = 0    # 0 - None, 1 - Warn, 2 - Debug, 3 - Error, 4 - All

    def log_message(self, level, tag, message):
        if self.log == 0:
            pass
        elif self.log == 1:
            if level == 1:
                print("WARN [", tag, "] :", message)
        elif self.log == 2:
            if level == 2:
                print("DEBUG [", tag, "] :", message)
        elif self.log == 3:
            if level == 3:
                print("ERROR [", tag, "] :", message)
        elif self.log == 4:
            if level == 1:
                print("WARN [", tag, "] :", message)
            if level == 2:
                print("DEBUG [", tag, "] :", message)
            if level == 3:
                print("ERROR [", tag, "] :", message)

    def handle_requests(self):
        for (socket, connection) in self.connections.items():
            if connection["processing"]:
                if connection["remaining"] <= 0:
                    self.log_message(2, connection["address"], "Request processed!")

                    connection["processing"] = False
                    connection["should_close"] = True

                    if connection["file"] is not None:
                        connection["file"].close()
                        connection["file"] = None
                else:
                    if connection["type"] == 0:
                        try:
                            read_chunk = connection["file"].read(self.chunk_size)
                        except IOError as ex:
                            self.log_message(3, connection["address"], "Error processing request: " + str(ex))
                        else:
                            connection["output"] += read_chunk
                            connection["remaining"] -= len(read_chunk)
            else:
                idx = connection["input"].find(b"\r\n\r\n")

                if idx >= 0:
                    _input = connection["input"]
                    request_string = _input[:idx + 4].decode()
                    connection["input"] = _input[idx + 4:]

                    request = HTTPRequest(request_string)
                    self.process_request(connection, request)

    def process_request(self, connection, request):
        connection["processing"] = True

        method = request.request_line[0]
        file_path = self.server_variables["document_root"] + "/public_html" + request.request_line[1]
        self.log_message(2, connection["address"], str(method) + "," + str(file_path))
        version = request.request_line[2]

        if os.path.isfile(file_path):
            try:
                connection["file"] = open(file_path, "rb")
            except IOError as ex:
                # TODO: add correct response
                self.log_message(3, connection["address"], ": Error opening requested file: " + str(ex))
            else:
                # Get the file extension
                (file_name, file_ext) = os.path.splitext(os.path.basename(file_path))

                # Get the size of the file
                # TODO: This is not the case with script files
                file_size = os.path.getsize(file_path)

                self.log_message(2, connection["address"], ": File '" + file_name + "." + file_ext[1:] +
                                 "' was found and was opened successfully! (" + str(file_size) + " bytes)")

                connection["output"] += b"HTTP/1.0 OK 200\r\nContent-Length:" + str(file_size).encode() + b"\r\n\r\n"

                connection["processing"] = True
                connection["remaining"] = file_size
                connection["should_close"] = False
                if method == "GET":
                    connection["type"] = 0   # READ

        elif os.path.isdir(file_path):
                print("TODO: List directory")
        else:
            print("TODO: handle invalid path (404 - File Not Found)")

    def handle_inputs(self, read):
        for sock in read:
            # A new connection
            if sock is self.server_socket:
                (client_socket, client_address) = self.server_socket.accept()

                client_socket.setblocking(False)
                self.input_list.append(client_socket)

                if client_socket in self.connections.keys():
                    self.log_message(1, "SERVER", "Socket already in the connections array!")

                self.connections[client_socket] = {"address"     : client_address,        # Client address
                                                   "input"       : b"",                   # Input buffer for this connection
                                                   "output"      : b"",                   # Output buffer for this connection
                                                   "file"        : None,                  # The requested resource
                                                   "remaining"   : 0,                     # How much data is left to process
                                                   "processing"  : False,                 # Are we currently processing a request
                                                   "type"        : 0,                     # Type of request: 0 - read, 1 - write
                                                   "should_close": False}                 # Should the connection be closed
                self.log_message(2, client_address, "Connect")
            else:
                # Get information about socket
                if sock in self.connections.keys():
                    connection = self.connections[sock]
                else:
                    self.log_message(1, "SERVER", "Closed socket error...")
                    continue

                # Receive data
                try:
                    receive_data = sock.recv(self.chunk_size)
                except socket.error as ex:
                    error = ex.args[0]

                    if not (error == errno.EWOULDBLOCK or error == errno.EAGAIN):
                        self.log_message(3, connection["address"], ": Error while receiving: " + ex.args[1])

                        self.close_connection(sock, connection)
                else:
                    # We have received data
                    if receive_data:
                        self.log_message(2, connection["address"], "Received " + str(len(receive_data)) + " bytes: " +
                                         receive_data.decode().replace("\r\n", "|"))
                        connection["input"] += receive_data

                        if sock not in self.output_list:
                            self.output_list.append(sock)

                    # Interpret empty result as closed connection
                    #elif connection["should_close"]:
                    else:
                        self.log_message(2, connection["address"], "Disconnect")

                        self.close_connection(sock, connection)

    def close_connection(self, sock, connection):

        self.log_message(2, connection["address"], "Closing ...")

        if connection["file"] is not None:
            connection["file"].close()

        if sock in self.input_list:
            self.input_list.remove(sock)

        if sock in self.output_list:
            self.output_list.remove(sock)

        if sock in self.connections.keys():
            del self.connections[sock]

        try:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        except socket.error:
            pass

    def handle_outputs(self, write):
        for sock in write:
            if sock in self.connections.keys():
                connection = self.connections[sock]
            else:
                self.log_message(1, "SERVER", "Closed socket error...")
                continue

            # If there is data to be sent
            if len(connection["output"]) > 0:
                # Send it
                send = sock.send(connection["output"])

                # Remove the sent data from the buffer
                data = connection["output"]
                send_data = data[:send]
                remaining = data[send:]
                connection["output"] = remaining
                self.log_message(2, connection["address"], "Send " + str(send) + " bytes of data: " +
                                 send_data.decode().replace("\r\n", "|"))
            elif connection["should_close"]:
                self.log_message(2, connection["address"], "Forced close")

                self.close_connection(sock, connection)

    def handle_errors(self, error):
        for sock in error:
            if sock is self.server_socket:
                self.log_message(3, "SERVER", "Internal server error: an error occurred on a socket!")
            else:
                if sock in self.connections.keys():
                    connection = self.connections[sock]
                else:
                    self.log_message(1, "SERVER", "Closed socket error...")
                    continue

                self.log_message(3, connection["address"], "Error has occurred!")
                self.close_connection(sock, connection)

    def serve_forever(self):
        while self.running:
            (read, write, error) = select.select(self.input_list, self.output_list, self.error_list, 0.01)

            self.handle_requests()
            self.handle_inputs(read)
            self.handle_outputs(write)
            self.handle_errors(error)

# ================================================================================================================
server = NonBlockingServer('localhost', 27017)
server.serve_forever()
