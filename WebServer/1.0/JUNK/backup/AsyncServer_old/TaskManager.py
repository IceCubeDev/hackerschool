__author__ = 'Ivan Dortulov'

from AsyncServer.EventDispatcher import *
import threading
import queue


class Task(threading.Thread, EventDispatcher):

    def __init__(self, type, file):

        super(Task, self).__init__()

        self.file = None
        self.type = type
        self.file_path = file
        self.done = False

    def run(self):

        if not self.file:

            if self.type == Task.TASK_READ:
                try:
                    self.file = open(self.file_path, "rb")

                except IOError as error:
                    ev = Event(Event.TASK_UPDATE, (self, error, None))
                    self.dispatch_event(ev)

                else:
                    while not self.done:
                        piece = self.file.read(1024)

                        if not piece:
                            self.done = True
                            self.file.close()

                            # We are done with this task, wohoo~!
                            ev = Event(Event.TASK_DONE, self)
                            self.dispatch_event(ev)
                        else:
                            # Update progress
                            ev = Event(Event.TASK_UPDATE, (self, None, piece))
                            self.dispatch_event(ev)

    (TASK_NULL, TASK_READ, TASK_COPY, TASK_WRITE) = range(0, 4)


class TaskManager(EventDispatcher):

    def __init__(self):

        super(TaskManager, self).__init__()

        self.tasks = []

    def handle_event(self, event):

        if event.code == Event.TASK_START:
            task = Task(event.data)
            task.add_event_listener(self, Event.TASK_DONE)
            self.tasks.append(task)
            task.start()