__author__ = 'Ivan Dortulov'


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