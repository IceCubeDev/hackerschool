__author__ = 'Ivan Dortulov'

from web.threaded.WorkerThread import *

import queue
import logging


class ThreadPool(object):

    def __init__(self, server, count=50):
        print("Creating thread pool with " + str(count) + " threads.")
        self.requests = []

        self.server = server

        self.workers = []
        for i in range(count):
            thread = WorkerThread(i, self.server)
            self.workers.append(thread)
            thread.start()

    def add_task(self, request, client_address):
        self.requests.append(request)

    def handle_next(self):

        for thread in self.workers:
            while thread.has_free_slots():
                if len(self.requests) > 0:
                    request = self.requests.pop()
                    thread.add_new_connection(request)
                else:
                    break