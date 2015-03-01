## @package EventDispatcher
# The EventDispatcher module contains classes used to implement the <i>Observer Pattern</i>.
#
# It consists of three main components Event, EventHandler and EventDispatcher.
#
# Events can be anything inside your application from a user clicking a button, a file being opened,
# a socket being closed to a thread finishing its execution. It is used for communication between
# the components of the AsyncServer.
#
# The EventHandler is an abstract class containing only one method called handle_event().
# Each EventHandler is associated with a given event code. When the event occurs the handle_event() method
# of the appropriate EventHandler is called to handle that event.
#
# The EventDispatcher class is used to dispatch messages to the EventHandler.
#

__author__ = 'Ivan Dortulov'

from abc import ABCMeta, abstractmethod

##
# Class representing a (handler, event code) pair.
#
# This class is internally used by the EventDispatcher class to maintain a list of event handlers.
# Each event handler is associated with the event code it is listening for.
class Entry(object):

    ##
    # Default constructor.
    #
    def __init__(self, handler, code):
        self.handler = handler
        self.code = code

##
# Class representing an event.
#
# Each event has a code, which is used by the EventDispatcher to determine which handler to invoke when calling
# the dispatch_event() method.
# The Event class has a field name data. It is used to transmit additional data along with the event.
#
class Event(object):

    ##
    # Default constructor.
    #
    def __init__(self, code, data = None):
        self.code = code
        self.data = data

    NULL = 0
    NETWORK_CONNECT = 2
    NETWORK_DISCONNECT = 3
    NETWORK_DATA = 4
    NETWORK_SEND = 5
    RECEIVED_REQUEST = 6
    TASK_START = 7
    TASK_UPDATE = 8
    TASK_DONE = 9
    TASK_DATA = 10

##
# Abstract class for event handlers.
#
# You do not need to inherit this class to be able to receive messages.
# All you need to do is inherit EventDispatcher and after that you will be able to
# send and receive messages.
class EventHandler():

    __metaclass__ = ABCMeta

    @abstractmethod
    ##
    # Method called when a certain event occurs.
    #
    # @param event The event that occurred.
    def handle_event(self, event):
        ...


##
# The EventDispatcher class is used for dispatching events.
#
# To give a class the ability to send and receive events all you need to do is
# inherit this class.
#
class EventDispatcher(EventHandler):

    ##
    # Default constructor.
    #
    def __init__(self):

        super(EventDispatcher, self).__init__()

        ## @var handlers
        # List of registered EventHandlers
        #
        self.handlers = []

    ##
    # Checks to see if a given EventHandler is already associated with a given event code.
    #
    # @param handler The EventHandler to check for.
    # @param code The event code to check for.
    # @return True is the EventHandler is already associated to the event code and False otherwis
    def has_event_listener(self, handler, code):

        for entry in self.handlers:
            if entry.handler is handler and entry.code == code:
                return True

        return False

    ##
    # Register an EventHandler to listen for an Event with code code.
    #
    # @param handler Handler to register,
    # @param code Event code that this handler is listening for.
    #
    def add_event_listener(self, handler, code):
        if not self.has_event_listener(handler, code):
            entry = Entry(handler, code)
            self.handlers.append(entry)

    ##
    # Stop an EventHandler from listening for a specific Event with code code.
    #
    # @param handler EventHandler to remove.
    # @param code Event code to remove.
    def remove_event_listener(self, handler, code):
        for entry in self.handlers:
            if entry.handler is handler and entry.code == code:
                self.handlers.remove(entry)

    ##
    # Stops a given EventHandler from listening to all event codes.
    #
    # @param handler The EventHandler to remove.
    #
    def remove_event_listener_all(self, handler):
        for entry in self.handlers:
            if entry.handler is handler:
                self.handlers.remove(entry)

    ##
    # Dispatch an event to all EventHandlers listening for that Event.
    #
    # @param event Event which to dispatch.
    def dispatch_event(self, event):
        for entry in self.handlers:
            if entry.code == event.code:
                entry.handler.handle_event(event)