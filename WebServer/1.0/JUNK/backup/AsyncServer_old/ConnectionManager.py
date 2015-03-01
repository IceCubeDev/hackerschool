## @package ConnectionManager
# The ConnectionManager module contains all of the necessary classes for handling a connection.
#
# It consists of two classes: Connection and ConnectionManager.
#
# The Connection class is just a simple representation of a connection. It contains
# a socket handle used to send and receive data, an input_buffer which stores the
# data received from the socket and an output_buffer from which data is sent to the
# socket.
#
# The ConnectionManager class creates the Connection objects. It receives messages from
# the WebServer class informing it when new connections have been established and when
# data has been received. It is responsible for managing the Connection objects.

__author__ = 'Ivan Dortulov'

from AsyncServer.EventDispatcher import *
from AsyncServer.HttpRequestHandler import *


##
# Class representing a byte buffer. It is used primarily to pass data
# between the HttpRequestHandler and the Connection classes
class Buffer(object):

    ##
    # Default constructor.
    #
    # Constructs an empty buffer.
    def __init__(self):
        self.buffer = b""

    ##
    # Write data to the buffer
    #
    def write(self, data):
        self.buffer += data

    ##
    # Read a single line from the buffer
    #
    # @param sep This parameter is optional. If set it will be used as line delimiter
    # @return Byte string
    #
    def read_line(self, sep=b"\r\n"):
        idx = self.buffer.find(sep)

        if idx >= 0:
            line = self.buffer[0:idx]
            self.buffer = self.buffer[idx + len(sep):]
        else:
            line = self.buffer
            self.buffer = b""

        return line

    ##
    # Obtain an array of lines.
    #
    # @param sep This parameter is optional. If set it will be used as line delimiter
    #
    def get_lines(self):
        lines = self.buffer.split(b"\n")
        return lines

    ##
    # Converts the buffer to a string
    #
    # @param decode This parameter is optional. If set the buffer will be decoded with the str.decode() method
    # @return String representation of the buffer.
    #
    def to_string(self, decode=False):
        if decode:
            return self.buffer.decode()

        return self.buffer

    ##
    # Checks to see if the buffer is not empty.
    #
    # @return Returns True if the buffer is empty and False otherwise.
    #
    def empty(self):
        if len(self.buffer) == 0:
            return True

        return False

    ##
    # Clear the buffer by emptying its contents.
    #
    def clear(self):
        self.buffer = b""

    ##
    # Returns the number of bytes inside the buffer.
    #
    # @return Size of the buffer in bytes,
    def length(self):
        return len(self.buffer)

    ##
    # Search the buffer for a substring.
    #
    # @param needle The substring to search for.
    #
    def find(self, needle):
        return self.buffer.find(needle)

    ##
    # Read a given number of bytes from the buffer by removing the read bytes from the buffer.
    #
    # @param bytes The number of bytes to read
    def read(self, bytes):
        data = self.buffer[0:bytes]
        self.buffer = self.buffer[bytes + 1:]
        return data

##
# Class representing a physical connection to the server.
#
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
        ## @var input_buffer
        # The input buffer where received data is stored.
        self.input_buffer = Buffer()
        ## @var output_buffer
        # The output buffer where data, which needs to be sent over the socket is stored.
        self.output_buffer = Buffer()
        ## @var handler
        # This is an instance of the HttpRequestHandler. It is responsible for
        # processing request and generating responses.
        self.handler = HttpRequestHandler(self)

    ##
    # Close this connection.
    #
    # Closes the connection by calling the close() method on the socket.
    def close_connection(self):
        self.socket.close()
        self.socket = None

## Class used for managing active connections.
#
# This class is responsible for creating, destroying and updating physical connections.
class ConnectionManager(EventDispatcher):

    ##
    # Default constructor.
    #
    def __init__(self):
        super(ConnectionManager, self).__init__()

        ## @var connections
        #  List of active connections.
        self.connections = []

        self.add_event_listener(self, Event.NETWORK_SEND)

    ##
    # Method inherited from EventHandler class.
    #
    # This is where the main logic of the class is realised. This method is called by the
    # WebServer class each time it submits an event. Here we create new Connections objects
    # when a connection is established, we close connections which are no longer active and
    # process received data.
    #
    # @param event The event that triggered this function.
    def handle_event(self, event):

        if event.code == Event.NETWORK_CONNECT:
            print("Creating connection.")
            connection = Connection(event.data)
            self.add_event_listener(connection.handler, Event.NETWORK_DATA)
            connection.handler.add_event_listener(self, Event.NETWORK_SEND)
            self.connections.append(connection)

        elif event.code == Event.NETWORK_DISCONNECT:
            print("Closing connection")
            con = self.find_connection(event.data)

            if con is not None:
                self.connections.remove(con)
                con.close_connection()
                del con

        elif event.code == Event.NETWORK_DATA:
            print("Processing data")
            (socket, data) = event.data
            con = self.find_connection(socket)
            if con is not None:
                self.dispatch_event(Event(Event.NETWORK_DATA, data))
                #print(data)

        elif event.code == Event.NETWORK_SEND:
            print("Sending data")
            con = event.data
            data = con.output_buffer.read(256)
            print(data)
            con.socket.sendall(data)

            if not con.output_buffer.empty():
                self.dispatch_event(Event(Event.NETWORK_SEND, con))

    ##
    # Iterate through the list of connections and search for a connection associated with socket.
    #
    # If the function succeeds it returns the connection object associated with the socket. If no
    # such connection is found, the function returns None.
    #
    # @param socket The socket to search for.
    # @return Connection object associated with socket or \b None if no such connection was found.
    def find_connection(self, socket):

        for con in self.connections:
            if con.socket is socket:
                return con

        return None