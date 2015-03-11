__author__ = 'Ivan Dortulov'

import WebServer

if __name__ == '__main__':
    server = WebServer.WebServer("localhost", 27015)
    server.serve_forever()