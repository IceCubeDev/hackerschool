__author__ = 'Ivan Dortulov'


class Log(object):

    def __init__(self, log_file):
        self.file = open(log_file, "w")
        self.file.write('<?xml version="1.0"?>\n')
        self.file.write('<history>\n')

    def log_event(self, type, sender, parent, data=""):
        event = ""

        if type == "connect" or type == "disconnect" or type == "disconnect0":
            event = "\t<event from=\"" + str(sender) + "\" value=\"" + type + "\" parent=\"" + parent + "\"/>\n"
        elif type == "receive" or type == "request_detected" or type == "request_set" or \
             type == "send" or type == "request_processed" or type == "request_response":
            event = "\t<event from=\"" + str(sender) + "\" value=\"" + type + "\" parent=\"" + parent + "\">\n"
            event += "\t\t<data size=\""+str(len(data)) + "\">"
            event += data
            event += "\t\t</data>\n"
            event += "\t</event>\n"
        elif type == "error":
            event = "\t<event from=\"" + str(sender) + "\" value=\"" + type + "\" parent=\"" + parent + "\">"
            event += data
            event += "\t</event>\n"

        self.file.write(event)

    def close(self):
        self.file.write("</history>\n")
        self.file.flush()
        self.file.close()