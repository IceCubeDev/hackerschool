__author__ = 'Ivan Dortulov'

from web.threaded import ThreadServer

thread_server = ThreadServer.ThreadServer('localhost', 27015)
thread_server.serve_forever()

print(__name__)