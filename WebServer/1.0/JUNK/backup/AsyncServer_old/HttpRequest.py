__author__ = 'Ivan Dortulov'

##
# This class represents an Http-Request to a server.
#
class HttpRequest(object):

    ##
    # Default constructor.
    #
    # Creates an empty Http-Request.
    def __init__(self):

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
        # Collection of form variables.
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
        self.referrer = "";

        ## @var user_agent
        # Raw user agent string of the client browser.
        #
        self.user_agent = "";

        ## @var user_host_address
        # The IP host address of the remote client.
        #
        self.user_host_address = "";

        ## @var user_host_name
        # The DNS name of the remote client.
        #
        self.user_host_name = "";

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
            print (key, ":", value)