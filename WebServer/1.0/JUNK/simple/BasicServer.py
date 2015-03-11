__author__ = 'Ivan Dortulov'

from Connection import Connection
from WorkerThread import WorkerThread
import select
import socket
import threading
import time
import sys


class BasicServer(object):

    def __init__(self, address, port):
        self.server_address = address
        self.server_port = port
        self.socket_family = socket.AF_INET
        self.socket_type = socket.SOCK_STREAM

        self.socket = socket.socket(self.socket_family, self.socket_type)

        self.socket.bind((self.server_address, self.server_port))
        self.socket.listen(10)
        self.socket.setblocking(False)

        self.connection_queue = []
        self.lock = threading.Lock()

        self.running = False

        self.worker = WorkerThread(self)

    def serve_forever(self):
        print("[MAIN] Started listening on ", self.server_address, ":", self.server_port)
        self.running = True

        self.worker.start()

        read_list = [self.socket, sys.stdin]

        while self.running:
            # Check for new connections
            (read, write, error) = select.select(read_list, [], [], 0)

            # We have received a new connection
            for input in read:
                if input is self.socket:
                    # Accept the request
                    (request, client_address) = self.socket.accept()
                    request.setblocking(False)

                    # Add the request to the queue
                    self.connection_queue.append(Connection(request, client_address, self))

                    self.worker.log.log_event("connect", client_address, "main")

                    #print("[MAIN]", client_address, " has connected!")
                elif input is sys.stdin:
                    stuff = sys.stdin.readline().rstrip('\n')
                    if stuff == "exit":
                        self.running = False
                    else:
                        print("you typed %s" % (stuff))

            # If there are connections waiting to be server
            if len(self.connection_queue) > 0:
                for conn in self.connection_queue:
                    # Check the connection status.
                    # If its closed, i.e. all request from that connection
                    # were processed, remove it from the list
                    if conn.closed:
                        #print("[MAIN] Connection ", conn.client_address, " was closed! Removing from list ...")
                        self.connection_queue.remove(conn)
                    # There is more work to be done.
                    # Hand this connection to the thread (if free slots are available)
                    else:
                        if self.worker.has_free_slots():
                            # First acquire a lock so that we don't do something
                            # strange
                            self.lock.acquire()
                            if conn not in self.worker.connections:
                                conn.parent = self.worker
                                if not conn.closed:
                                    #print("[MAIN] Assigned ", conn.client_address, " to ", self.worker.name)
                                    self.worker.connections.append(conn)

                            self.lock.release()
                        else:
                            # No free slots, nothing more that can be done, the connection
                            # will have to wait
                            #print("[MAIN] No free slot for ", conn.client_address)
                            break

            # Sleep and let the thread work some
            time.sleep(0.001)

        self.socket.close()
        self.worker.running = False

# ==============================================================
server = BasicServer('127.0.0.1', 27015)
server.serve_forever()