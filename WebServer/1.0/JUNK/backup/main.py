__author__ = 'Ivan Dortulov'

from web.threaded.ThreadedServer import *
from web.async.AsyncServer import *

#thread_server = ThreadedServer('localhost', 27016)
#thread_server.server_forever()

async_server = AsyncServer('localhost', 27015)
async_server.serve_forever()