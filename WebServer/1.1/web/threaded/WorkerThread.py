__author__ = 'Ivan Dortulov'

from web.threaded.RequestHandler import RequestHandler

import threading
import time
import errno
import socket
import select


class WorkerThread(threading.Thread):

    def __init__(self, thread_id, server):
        threading.Thread.__init__(self)
        self.thread_id = thread_id

        self.connections = []
        self.handlers = {}
        self.server = server

        self.running = True

    def run(self):
        while self.running:
            for sock in self.connections:
                handler = self.get_handler(sock)

                if handler is not None:
                    handler.handle_next()

                    if len(handler.output) > 0:
                        try:
                            sent = sock.send(handler.output)
                        except IOError as ex:
                            print ("Error occurred!", ex)
                            self.close_connection(sock)
                            continue
                        else:
                            print("[Thread ", self.thread_id, "] Replied with  ",
                                   sent, " bytes to ", sock.getpeername(), handler.output[:sent])
                            handler.output = handler.output[sent:]
                    elif handler.should_close:
                        self.close_connection(sock)
                        continue

                    try:
                        recv_data = sock.recv(128)
                    except socket.error as ex:
                        error = ex.args[0]

                        if error == errno.EAGAIN or error == errno.EWOULDBLOCK:
                            continue
                        else:
                            print ("Error occurred!", ex)
                            self.close_connection(sock)
                    else:
                        if recv_data:
                            print("[Thread ", self.thread_id, "] Received ",
                                   len(recv_data), " bytes from ", sock.getpeername(), recv_data)
                            handler.receive_data(recv_data)
                        else:
                            print ("NO DATA")
                            self.close_connection(sock, False)

                else:
                    print("Key error, handler does not exist!")

            time.sleep(0.0001)

    def add_new_connection(self, request):
        print ("[Thread ", self.thread_id, "] Added new connection ", request.getpeername())
        request.setblocking(False)
        self.handlers[request] = RequestHandler(self.server)
        self.connections.append(request)

    def close_connection(self, request, call_close=True):
        self.connections.remove(request)
        del self.handlers[request]
        if call_close:
            print ("[Thread ", self.thread_id, "] Closing connection for ", request.getpeername())
            print ("[Thread ", self.thread_id, "] ", len(self.connections), "connections remain.")
            request.shutdown(socket.SHUT_RDWR)
            request.close()

    def has_free_slots(self):
        return len(self.connections) <= WorkerThread.MAX_CONNECTIONS

    def get_handler(self, request):
        if request in self.handlers.keys():
            return self.handlers[request]
        else:
            return None

    MAX_CONNECTIONS = 100