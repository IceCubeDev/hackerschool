__author__ = 'root'

from web.async.EventDispatcher import *
from web.HttpRequest import *
from web.HttpResponse import *
from web.async.TaskManager import *
import queue
import os

class Connection(EventDispatcher):

    ##
    # Default constructor.
    #
    # Sets the socket associated with this connection.
    # @param socket The connection socket
    def __init__(self, socket):

        super(Connection, self).__init__()

        ## @var socket
        # The socket associated with this connection.
        self.socket = socket

        self.input = b""
        self.output = b""
        self.current_request = None
        self.request_queue = queue.Queue()
        self.parent = None
        self.rfile = None
        self.wfile = None

        self.task_manager = TaskManager()

    def handle_current_request(self):
        if self.current_request is not None:
            if len(self.current_request.request_uri) > 1024:
                response = HttpResponse(400, "You have sent a request which has a query string which exceeds the maximum length supported by the server.")
                self.current_request.processed = True
                self.output += response.response

            else:
                if self.current_request.method == "GET":
                    print ("Handling GET request!")
                    # Get the requested resource
                    file_path = self.parent.server.document_root
                    file_path = file_path[:file_path.rfind("/")] + "/public_html" + self.current_request.request_uri
                    print (file_path)
                    #print (file_path)

                    if self.rfile is None:
                        if os.path.isfile(file_path):
                            print("Opening file on separate thread.")
                            task = Task(Task.READ_FILE, file_path)
                            task.add_event_listener(self, Event.TASK_START)
                            task.add_event_listener(self, Event.TASK_UPDATE)
                            task.add_event_listener(self, Event.TASK_DONE)

                            self.task_manager.add_task(task)
                        else:
                            if os.path.isdir(file_path):
                                listing = self.list_directory(file_path)

                                response = HttpResponse(200, (len(listing), "txt"))
                                self.output += response.response

                                self.output += listing.encode()
                                self.current_request.processed = True
                            else:
                                print ("File not found!")
                                response = HttpResponse(404, "The resource <b>" + file_path + "</b> could not be located by the server.")
                                self.output += response.response
                                self.current_request.processed = True

            if self.current_request.processed == True:
                try:
                    del self.current_request
                    _next = self.request_queue.get(False)
                except queue.Empty:
                    self.current_request = None
                else:
                    self.current_request = _next

    def list_directory(self, directory):
        listing = ""
        for root, dirs, files in os.walk(directory):
            level = root.replace(directory, '').count(os.sep)
            indent = ' ' * 4 * (level)
            listing += '{}{}/'.format(indent, os.path.basename(root)) + "\n"
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                listing += '{}{}'.format(subindent, f) + "\n"

        return listing

    def handle_event(self, event):
        if event.code == Event.TASK_START:
            if self.current_request is not None:
                print ("TASK_START")
                (task, size) = event.data
                name, ext = os.path.splitext(task.file_path)
                self.current_request.remaining = size

                response = HttpResponse(200, (size, ext))
                self.output += response.response

        elif event.code == Event.TASK_UPDATE:
            (task, error, chunk) = event.data

            if error:
                response = HttpResponse(404, chunk)
                self.output += response.response
            else:
                self.output += chunk

        elif event.code == Event.TASK_DONE:
            print("TASK_DONE")
            self.current_request.processed = True
            pass