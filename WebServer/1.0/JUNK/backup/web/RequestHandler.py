__author__ = 'Ivan Dortulov'


class RequestHandler(object):

    def __init__(self):
        self.request = None
        self.client_address = None
        self.server = None
        self.should_close = False

    ##
    # Called before the handle() method to perform any initialization actions required.
    #
    # The default implementation does nothing.
    #
    def setup(self):
        print ("Initializing the request handler ...")

    ##
    # This function must do all the work required to service a request.
    #
    # The default implementation does nothing. Several instance attributes are available to it;
    # the request is available as self.request; the client address as self.client_address;
    #  and the server instance as self.server, in case it needs access to per-server information.
    #
    def handle(self):
        print("Handling the request ...")

    ##
    # Called after the handle() method to perform any clean-up actions required.
    #
    # The default implementation does nothing. If setup() raises an exception, this function will not be called.
    def finish(self):
        print ("Terminating")
