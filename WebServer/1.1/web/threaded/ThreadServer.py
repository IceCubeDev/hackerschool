__author__ = 'Ivan Dortulov'

from web.threaded.ThreadPool import ThreadPool

import socket
import select
import os


class ThreadedServer(object):

    def __init__(self,
                server_name='localhost',
                server_port=27015,
                address_family=socket.AF_INET,
                socket_type=socket.SOCK_STREAM):

        self.socket = None
        self.server_address = server_name
        self.server_port = server_port
        self.address_family = address_family
        self.socket_type = socket_type

        self.thread_pool = ThreadPool(self, 10)

        self.document_root = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../../public_html")
        print (self.document_root)

        self.running = False

        self.server_bind()
        self.server_listen()

    def server_bind(self):
        print("Binding server ...")
        if self.socket is None:
            self.socket = socket.socket(self.address_family, self.socket_type)
            self.socket.bind((self.server_address, self.server_port))
            self.socket.setblocking(False)
        else:
            print("Server already bound to ", self.server_address, ":", self.server_port)
            pass

    def server_listen(self):
        #print("Starting listening ...")
        if self.socket is not None:
            self.socket.listen(5)
            self.running = True
        else:
            print("Server has not been started.")
            pass

    def serve_forever(self):
        print("Listening on " + self.server_address + ":" + str(self.server_port))

        read_list = [self.socket]
        while self.running:
            (read, write, error) = select.select(read_list, [], [], 0)

            for s in read:
                if s is self.socket:
                    (request, client_address) = self.socket.accept()

                    #print("Connection from ", request.getpeername(), " accepted! Adding task to thread pool...")

                    self.thread_pool.add_task(request, client_address)

            self.thread_pool.handle_next()