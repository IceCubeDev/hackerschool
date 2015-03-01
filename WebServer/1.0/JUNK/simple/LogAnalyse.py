__author__ = 'Ivan Dortulov'

class Client(object):

    def __init__(self, id):
        self.history = ["connect"]
        self.name = id


import xml.etree.ElementTree as ET
tree = ET.parse('/home/ivan/Documents/Python/SubTasking/log.xml')
root = tree.getroot()

clients = []

def find_client(id):
    for client in clients:
        if client.name == id:
            return client
    return None

for event in root.findall("event"):
    type = event.attrib["value"]

    if type == "connect":
        clients.append(Client(event.attrib["from"]))
    elif type == "disconnect":
        id = event.attrib["from"]
        client = find_client(id)
        if client is not None:
            client.history.append("disconnect")
    elif type == "disconnect0":
        id = event.attrib["from"]
        client = find_client(id)
        if client is not None:
            client.history.append("client disconnect")
    elif type == "receive":
        id = event.attrib["from"]
        data = event.find('data')
        client = find_client(id)

        if client is not None:
            client.history.append("recv: " + data.text.replace("\n", " | "))

    elif type == "send":
        id = event.attrib["from"]
        data = event.find('data')
        client = find_client(id)

        if client is not None:
            client.history.append("send: " + data.text.replace("\n", " | "))
    elif type == "error":
        id = event.attrib["from"]
        client = find_client(id)

        if client is not None:
            client.history.append("error: " + event.text)

for client in clients:
    print(client.name)
    for event in client.history:
        print("\t", event)