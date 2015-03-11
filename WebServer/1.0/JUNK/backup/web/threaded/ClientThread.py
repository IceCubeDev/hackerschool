__author__ = 'Ivan Dortulov'

import threading


class ClientThread(threading.Thread):

    def __init__(self, _id, handler):
        threading.Thread.__init__(self)

        self.handler = handler
        self.handler.parent = self
        self.thread_id = _id
        self.should_close = False

    def run(self):
        self.handler.setup()

        while not self.should_close:
            self.handler.handle()

        self.handler.finish()