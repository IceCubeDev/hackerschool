__author__ = 'Ivan Dortulov'

from web.threaded.WorkerThread import *
from web.threaded.HttpRequestHandler import *

import socket
import select
import os
import threading
import queue
import sys


class ThreadServer(object):

    def __init__(self,
                 server_name='localhost',
                 server_port=27015,
                 address_family=socket.AF_INET,
                 socket_type=socket.SOCK_STREAM,
                 handler=HttpRequestHandler):

        self.socket = None
        self.server_address = server_name
        self.server_port = server_port
        self.address_family = address_family
        self.socket_type = socket_type
        self.running = False
        self.document_root = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../../public_html")
        self.handler_class = handler
        self.lock = threading.Lock()
        self.connections = queue.Queue()

        print("[MAIN] Initializing the server ...")
        self.server_bind()
        self.server_listen()

    def server_bind(self):
        if self.socket is None:
            try:
                self.socket = socket.socket(self.address_family, self.socket_type)
                self.socket.bind((self.server_address, self.server_port))
                #self.socket.setblocking(False)
            except socket.error as ex:
                print("[ERROR]", ex)
                sys.exit(0)

    def server_listen(self):
        if self.socket is not None:
            self.socket.listen(5)
            self.running = True

    def serve_forever(self):
        print("Listening on " + self.server_address + ":" + str(self.server_port))

        for i in range(0, 10):
            thread = WorkerThread(self.lock, self, self.connections, self.handler_class)
            thread.start()

        read_list = [self.socket]
        while self.running:
            # Polling select
            (read, write, error) = select.select(read_list, [], [], 0)

            for sock in read:
                (request, client_address) = sock.accept()
                print("[MAIN] New connection from ", request.getpeername())
                self.lock.acquire()
                try:
                    print("[MAIN] Added ", request.getpeername(), " to the queue!")
                    self.connections.put(request)
                finally:
                    self.lock.release()

            time.sleep(0.001)