__author__ = 'Ivan Dortulov'

import threading
import time
import socket
import errno


class WorkerThread(threading.Thread):

    MAX_CONNECTIONS = 100
    WAIT = 0.001 / MAX_CONNECTIONS
    PACKET_SIZE = 512

    def __init__(self, lock, server, connections, handler):
        threading.Thread.__init__(self)
        self.lock = lock
        self.connections = connections
        self.running = True
        self.local = threading.local()
        self.response = b""
        self.should_close = False
        self.handler_class = handler
        self.server = server
        print("[", self.name, "] Created!")

    def run(self):
        self.local.requests = []
        print("[", self.name, "] Started!")

        while self.running:
            # if we are not handling a request
            if len(self.local.requests) < WorkerThread.MAX_CONNECTIONS:
                #print("[", self.name, "] Free slots available!")
                # acquire the request queue lock
                self.lock.acquire()
                # if there is something in the queue
                if not self.connections.empty():
                    # get a request
                    self.local.request = self.connections.get(False)
                    self.local.request.setblocking(False)
                    self.local.requests.append(self.handler_class(self.local.request, self))
                    # release the lock
                    self.lock.release()
                    print("[", self.name, "] Processing requests from ", self.local.request)
                # no request available
                else:
                    # just release the lock
                    self.lock.release()

            for handler in self.local.requests:
                handler.process_current()

                # if there is data to be sent to the client
                if len(handler.output) > 0:
                    # try sending the data (in WorkerThread.PACKET_SIZE byte chunks)
                    try:
                        sent = handler.socket.send(handler.output[:WorkerThread.PACKET_SIZE])
                    # Something went wrong
                    except IOError as ex:
                        error = ex.args[0]

                        if error == errno.EAGAIN or error == errno.EWOULDBLOCK:
                            print("[", self.name, "] socket.send: EAGAIN, EWOULDBLOCK ->", handler.socket)
                            continue
                        else:
                            print("[", self.name, "] Error occurred while sending:\n", error)
                            handler.socket.close()
                            self.local.requests.remove(handler)
                            del handler
                            continue

                    # the data was successfully sent
                    else:
                        # update the data which remains to be sent
                        handler.output = handler.output[sent:]
                        print("[", self.name, "] Sent ", sent, " bytes to ", handler.socket)
                        continue

                # No more data to send, should we close the connection?
                elif handler.should_close:
                    print("[", self.name, "] Closing connection for ", handler.socket)
                    handler.socket.close()
                    self.local.requests.remove(handler)
                    del handler
                    continue

                # Try to receive data
                try:
                    self.local.receive_data = handler.socket.recv(WorkerThread.PACKET_SIZE)
                except socket.error as ex:
                    error = ex.args[0]

                    # Is there data available?
                    if error == errno.EAGAIN or error == errno.EWOULDBLOCK:
                        continue
                    else:
                        # A real error has occurred
                        print("[", self.name, "] Error occurred while receiving:\n", error)
                        handler.socket.close()
                        self.local.requests.remove(handler)
                        del handler
                        continue
                else:
                    # We have received data
                    if self.local.receive_data:
                        print("[", self.name, "] Received ", len(self.local.receive_data), " bytes from ", handler.socket)
                        handler.handle_data(self.local.receive_data)
                    # Normal disconnect
                    else:
                        print("[", self.name, "] Received 0 bytes from ", handler.socket)
                        handler.socket.close()
                        self.local.requests.remove(handler)
                        del handler

            time.sleep(0.001)