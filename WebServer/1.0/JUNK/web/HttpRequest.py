__author__ = 'Ivan Dortulov'

import re


##
# This class represents an Http-Request to a server.
#
class HttpRequest(object):

    ##
    # Default constructor.
    #
    # Creates an empty Http-Request.
    def __init__(self, request_string = ''):

        ## @var contentEncoding
        # The character set of the entity-body.
        # Default: utf-8.
        self.contentEncoding = "utf-8"

        ## @var contentLength
        # The length, in bytes, of content sent by the client.
        # Default: 0.
        self.contentLength = 0

        ## @var content_type
        # MIME content type of the request.
        # Default: text/plain.
        self.content_type = "text/plain"

        ## @var cookies
        # A collection of cookies sent by the client.
        self.cookies = []

        ## @var form
        # Collection of form variables. Same as query_string.
        self.form = {}

        ## @var headers
        #  Collection of HTTP headers.
        self.headers = {}

        ## @var method
        # The HTTP data transfer method (such as GET, POST, or HEAD) used by the client.
        # Default: GET.
        #
        self.method = "GET"

        ## @var query_strings
        # A collection of HTTP query string variables.
        #
        # For example http://www.contoso.com/default.aspx?fullname=Ivan%20Dortulov has a
        # query string fullname=Ivan Dortulov).
        #
        self.query_strings = {}

        ## @var referrer
        # Information about the URL of the client's previous request that linked to the current URL.
        self.referrer = ""

        ## @var user_agent
        # Raw user agent string of the client browser.
        #
        self.user_agent = ""

        ## @var user_host_address
        # The IP host address of the remote client.
        #
        self.user_host_address = ""

        ## @var user_host_name
        # The DNS name of the remote client.
        #
        self.user_host_name = ""

        ## @var user_languages
        # Sorted string array of client language preferences.
        # Default: en-us.
        #
        self.user_languages = ["en-us"]

        ## @var request_uri
        # The request uri.
        # Default: / - The server root.
        #
        self.request_uri = "/"

        ## @var http_version
        # Protocol version.
        # Default: 1.1
        #
        self.http_version = 1.1

        self.processed = False
        self.remaining = 0

        if len(request_string) > 0:
            self.from_string(request_string)

    ##
    # Print the response to the console.
    #
    def dump(self):
        print ("------> Request-line:")
        result = self.method + " "
        result += self.request_uri + "?"
        for key,value in self.query_strings.items():
            result += key + "=" + value + "&"

        result = result[0:-1]
        result += " HTTP/" + str(self.http_version)
        print (result)

        print ("------> Query String:")
        for key, value in self.query_strings.items():
            print (key, "=", u''.join(value))

        print ("------> Headers:")
        for key, value in self.headers.items():
            print(key, ":", value)

    def from_string(self, request_string):
        request_line = HttpRequest.check_request_line.match(request_string)

        if request_line is not None:
            #print (request_line.group(0))
            self.method = request_line.group(1)
            self.request_uri = request_line.group(2)

            self.http_version = float(request_line.group(4))

            if self.method == "GET":
                idx = self.request_uri.find("?")
                if idx >= 0:
                    uri = self.request_uri[:idx]
                    data = self.request_uri[idx+1:]
                    self.request_uri = uri

                    pairs = data.split("&")
                    for pair in pairs:
                        query = HttpRequest.check_query_string.match(pair)
                        if query is not None:
                            self.query_strings[query.group(1).lower()] = query.group(2)
                            self.form[query.group(1).lower()] = query.group(2)

            request_string = request_string[len(request_line.group(0)) + 1:]

        while True:
            if len(request_string) == 0:
                break

            header = HttpRequest.check_header.match(request_string)
            if header is not None:
                self.headers[header.group(1).lower()] = header.group(2)
                #print (header.group(1).lower(), ":", header.group(2))

                request_string = request_string[len(header.group(0)):]
            else:
                break


    check_request_line = re.compile("(.*)\s(.*)(?=\sHTTP)(\sHTTP\/)([1]\.[0-1])\s")
    check_header = re.compile("(.*):\s(.*)\s")
    check_query_string = re.compile("(.*)=(.*)")

    MAX_HEADER_LENGTH = 8192