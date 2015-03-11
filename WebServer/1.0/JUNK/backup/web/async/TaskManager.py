__author__ = 'Ivan Dortulov'

from web.async.EventDispatcher import *
import queue
import threading
import os


class Task(EventDispatcher, threading.Thread):

    def __init__(self, type, file_path):
        super(Task, self).__init__()

        self.type = type
        self.file_path = file_path
        self.file = None
        self.remaining = 0
        self.finished = False
        threading.Thread.__init__(self)
        self.running = True

    def run(self):
        while self.running:
            if self.file is None:
                mode = "rb"

                if self.type == Task.READ_FILE:
                    mode = "rb"
                elif self.type == Task.WRITE_FILE:
                    mode = "wb"

                try:
                    self.file = open(self.file_path, mode)
                except IOError:
                    self.dispatch_event(Event(Event.TASK_UPDATE, (self, True, "Unable to open file!")))
                else:
                    size = os.path.getsize(self.file_path)
                    self.remaining = size
                    self.dispatch_event(Event(Event.TASK_START, (self, size)))

            elif self.remaining > 0:
                #print("Chunk")
                if self.type == Task.READ_FILE:
                    if self.remaining > 128:
                        data = self.file.read(128)
                        self.remaining -= 128
                        self.dispatch_event(Event(Event.TASK_UPDATE, (self, False, data)))
                    else:
                        data = self.file.read(self.remaining)
                        self.remaining = 0
                        self.running = False
                        self.finished = True
                        self.file.close()
                        self.file = None

                        self.dispatch_event(Event(Event.TASK_UPDATE, (self, False, data)))
                        self.dispatch_event(Event(Event.TASK_DONE, self))

    READ_FILE = 0
    WRITE_FILE = 1

class TaskManager(EventDispatcher):

    def __init__(self):
        super(TaskManager, self).__init__()

        self.current_task = None
        self.task_queue = queue.Queue()

    def add_task(self, task):
        if self.current_task is None:
            print("Starting new task for file ", task.file_path)

            task.add_event_listener(self, Event.TASK_DONE)
            task.start()
            self.current_task = task
        else:
            self.task_queue.put(task)

    def handle_event(self, event):
        if event.code == Event.TASK_DONE:
            try:
                _next = self.task_queue.get(False)
            except queue.Empty:
                self.current_task = None
            else:
                del self.current_task
                self.current_task = _next