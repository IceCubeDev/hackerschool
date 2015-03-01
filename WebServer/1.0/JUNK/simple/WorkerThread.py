__author__ = 'Ivan Dortulov'

from Connection import Connection
import threading
import errno
import time
import socket
from Log import *


class WorkerThread(threading.Thread):

    MAX_CONNECTIONS = 100

    def __init__(self, server):
        threading.Thread.__init__(self)

        self.server = server
        self.lock = self.server.lock
        self.connections = []

        self.running = True
        self.log = Log("/home/ivan/Documents/Python/SubTasking/log.xml")

    def run(self):
        while self.running:
            if self.lock.acquire(False):
                # If there are connections waiting processing
                if len(self.connections) > 0:
                    # Get the connection at the top of the list
                    connection = self.connections.pop()

                    # If there is data pending to be sent to this connection
                    if len(connection.output) > 0:
                        # Get a chunk of the data
                        data = connection.output[:Connection.CHUNK_SIZE]
                        # Try to send that data to the client
                        try:
                            sent = connection.socket.send(data)
                        except socket.error as ex:
                            error = ex.args[0]

                            #Check for errors
                            if not (error == errno.EAGAIN or error == errno.EWOULDBLOCK):
                                self.log.log_event("error", connection.client_address, self.name, "send: " + ex.args[0])
                                print("[ERROR] socket.send:", ex)
                                connection.close()
                        else:
                            # We have sent some data to the connection. Update the buffer.
                            send_data = connection.output[:sent]
                            connection.output = connection.output[sent:]
                            self.log.log_event("send", connection.client_address, self.name, send_data.decode())

                    # There is no data to be sent to the client.
                    # If the connection should close, close it
                    elif connection.should_close:
                        self.log.log_event("disconnect", connection.client_address, self.name)
                        connection.close()

                    # if you call recv on a closed socket,
                    # you're gonna have a bad time
                    if not connection.closed:
                        # Try to receive data from the connection
                        try:
                            recv_data = connection.socket.recv(Connection.CHUNK_SIZE)
                        except socket.error as ex:
                            error = ex.args[0]

                            # Check for errors
                            if not (error == errno.EAGAIN or error == errno.EWOULDBLOCK):
                                self.log.log_event("error", connection.client_address, self.name, "recv: " + ex.args[0])
                                connection.close()
                        else:
                            # If we received data
                            if recv_data:
                                # Process it
                                self.log.log_event("receive", connection.client_address, self.name, recv_data.decode())
                                connection.handle_data(recv_data)
                            else:
                                # We received 0 bytes which means that
                                # the client has disconnected
                                self.log.log_event("disconnect0", connection.client_address, self.name)
                                connection.close()

                        # Process requests
                        connection.handle_next_request()

                self.lock.release()

            # Rest ... for now :D
            time.sleep(0.001)

        for conn in self.connections:
            if not conn.closed:
                conn.close()
                self.connections.remove(conn)
                del conn

        self.log.close()

    def has_free_slots(self):
        return len(self.connections) < WorkerThread.MAX_CONNECTIONS