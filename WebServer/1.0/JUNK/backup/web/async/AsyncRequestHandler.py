__author__ = 'Ivan Dortulov'

from web.RequestHandler import *
from web.async.EventDispatcher import *
from web.async.Connection import *
from web.HttpRequest import *
from web.HttpResponse import *


class AsyncRequestHandler(RequestHandler, EventDispatcher):

    def __init__(self):

        super(AsyncRequestHandler, self).__init__()

        self.connections = []

    def handle_event(self, event):
        if event.code == Event.NETWORK_CONNECT:
            connection = Connection(event.data)
            connection.parent = self
            self.connections.append(connection)

        elif event.code == Event.NETWORK_DATA:
            (socket, data) = event.data
            con = self.find_connection(socket)

            con.input += data

            clrf = con.input.find(b"\r\n\r\n")

            # Check if we have received end of Http-Headers
            if clrf >= 0:
                print ("Request detected!")
                # Get the request as a string
                request_string = con.input[:clrf + 4]

                # Parse the request string and create a HttpRequest object
                request = HttpRequest(request_string.decode())

                if con.current_request is None:
                    # Set the current request
                    con.current_request = request
                    con.input = con.input[clrf + 4:]
                else:
                    con.request_queue.put(request)

            elif len(con.input) > HttpRequest.MAX_HEADER_LENGTH:
                con.input = ""
                response = HttpResponse(400, "You have sent a request which has a query string which exceeds the maximum length supported by the server.")
                con.output += response.response

            con.handle_current_request()

        elif event.code == Event.NETWORK_SEND:
            con = self.find_connection(event.data)

            if con is not None:
                if len(con.output) > 0:
                    data = con.output[0:256]
                    con.output = con.output[256:]
                    #print (data)
                    #print ("Returning: ", data)

                    try:
                        con.socket.sendall(data)
                    except IOError:
                        pass

        elif event.code == Event.NETWORK_DISCONNECT:
            con = self.find_connection(event.data)
            self.close_connection(con)

    def find_connection(self, socket):
        for con in self.connections:
            if con.socket is socket:
                return con

    def close_connection(self, con):
        con.socket.close()
        self.connections.remove(con)
        del con