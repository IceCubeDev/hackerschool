__author__ = 'Ivan Dortulov'

from web.BaseServer import *
from web.RequestHandler import *
from web.threaded.ClientThread import *
from web.threaded.ThreadedRequestHandler import *
import socket


class ThreadedServer(BaseServer):

    def __init__(self, address, port, handler=ThreadedRequestHandler):
        ThreadedServer.address_family = socket.AF_INET
        ThreadedServer.socket_type = socket.SOCK_STREAM

        self.threads = []
        self.thread_id_counter = 0

        super(ThreadedServer, self).__init__(address, port, handler)

    def process_request(self, request, client_address):
        handler = self.RequestHandlerClass()
        handler.request = request
        handler.client_address = client_address
        handler.server = self

        thread = ClientThread(self.thread_id_counter, handler)
        self.thread_id_counter += 1
        self.threads.append(thread)
        thread.start()

    def shutdown(self):
        for thread in self.threads:
            thread.should_close = True
            self.threads.remove(thread)
            del thread