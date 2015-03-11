__author__ = 'Ivan Dortulov'

from HttpRequest import HttpRequest
import queue


class Connection(object):

    # Argument for recv and send
    CHUNK_SIZE = 256

    def __init__(self, socket, client_address, server):
        self.server = server
        self.socket = socket
        self.client_address = client_address
        self.parent = None

        self.input = b""
        self.output = b""

        self.closed = False
        self.should_close = False

        # Request currently being handled.
        # A connection can send more than one request
        self.current_request = None
        # Queue for unhandled requests
        self.request_queue = queue.Queue()

    # Handle data received from the connection
    def handle_data(self, data):
        self.input += data

        idx = self.input.find(b"\r\n\r\n")

        if idx >= 0:
            # Get the http headers
            header_string = self.input[:idx]

            # Remove what we have read from the input
            self.input = self.input[idx+4:]

            # Parse the request
            request = HttpRequest(header_string.decode())

            # Add request to request queue
            self.request_queue.put(request)

            if self.parent is not None:
                self.parent.log.log_event("request_detect", self.client_address, self.parent.name,
                                          header_string.decode())

    # Close the connection
    def close(self):
        self.socket.close()
        self.closed = True

    # Handle the next request in the request queue
    def handle_next_request(self):
        # If we are not processing a request
        if self.current_request is None:
            # Check to see if there are requests to be processed
            if not self.request_queue.empty():
                self.current_request = self.request_queue.get(False)
                self.parent.log.log_event("request_set", self.client_address, self.parent.name,
                                          self.current_request.request_string)
        # We are already processing a request
        else:
            # If we are finished processing the request
            if self.current_request.processed:
                # Free memory
                self.parent.log.log_event("request_processed", self.client_address, self.parent.name,
                                          self.current_request.request_string)
                del self.current_request
                self.current_request = None
            # If there is more work to be done
            else:
                data = b"Congratulations!"

                response = b"HTTP/1.0 200 OK\r\n"
                response += b"Connection: close\r\n"
                response += b"Content-Length:" + str(len(data)).encode() + b"\r\n\r\n"
                response += data

                self.output += response
                self.current_request.processed = True
                self.current_request.remaining = 0
                self.should_close = True
                self.parent.log.log_event("request_response", self.client_address, self.parent.name,
                                          response.decode())