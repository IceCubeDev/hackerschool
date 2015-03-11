__author__ = 'Ivan Dortulov'


class HttpRequest(object):

    def __init__(self, header_string):
        self.processed = False
        self.remaining = 0
        self.request_string = header_string