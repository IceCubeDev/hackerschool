__author__ = 'Ivan Dortulov'

import re


class HTTPRequest(object):

    def __init__(self, request_string):

        idx = request_string.find("\n")
        self.request_line = request_string[:idx].split()
        request_string = request_string[idx + 1:]

        self.headers = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", request_string))
        self.request_path = self.request_line[1]

        # print(self.request_line)
        # print(self.headers)