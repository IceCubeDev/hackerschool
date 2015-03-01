__author__ = 'Ivan Dortulov'

from NonBlockingServer import *

if __name__ == "__main__":
    server = NonBlockingServer('localhost', 27015)
    server.serve_forever()
