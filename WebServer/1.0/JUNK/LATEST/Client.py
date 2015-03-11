__author__ = 'Ivan Dortulov'

import optparse
import socket
import threading
import errno


class Worker(threading.Thread):
    def __init__(self, address, number, id):
        threading.Thread.__init__(self)
        self.socket = None
        self.requests = number
        self.completed_requests = 0
        self.running = True
        self.address = address
        self.id = id
        self.output = b""
        self.current_id = id

    def run(self):
        while self.running:
            if self.requests > 0:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect(self.address)
                self.socket.setblocking(False)

                print("\n[", self.name, "]Client #" + str(self.current_id) + " Connect")

                self.output = b"Hello from client #" + str(self.current_id).encode()

                while len(self.output) > 0:
                    try:
                        send = self.socket.send(self.output)
                    except socket.error as ex:
                        print("[", self.name, "] Error occurred: ", ex.args[0], ex.args[1])
                        self.running = False
                        break
                    else:
                        print("[", self.name, "] Client #" + str(self.current_id) + " Send: ", self.output[:send])
                        self.output = self.output[send:]

                while True:
                    try:
                        receive_data = self.socket.recv(1024)
                    except socket.error as ex:
                        error = ex.args[0]

                        if error == errno.EWOULDBLOCK or error == errno.EAGAIN:
                            continue
                        else:
                            print("[", self.name, "] Error occurred: ", ex.args[0], ex.args[1])
                            self.running = False
                            break
                    else:
                        if receive_data:
                            print("[", self.name, "] Client #" + str(self.current_id) + " Reply: ", receive_data)
                        else:
                            self.socket.close()
                            self.completed_requests += 1
                            break

                self.requests -= 1
                self.current_id += 1
            else:
                self.running = False
                print("[", self.name, "] ", self.completed_requests, " request completed!")


def run_tests(address, port, path, number, concur, data=""):

    if concur == 1:
        for i in range(0, number):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((address, port))
            print("\nClient #" + str(i) + " Connect")
            if len(data) == 0:
                data = "Hello from Client# " + str(i) + "\r\n"

            while len(data) > 0:
                send = sock.send(data.encode())
                print("Client #" + str(i) + " Send: ", data[:send].encode())
                data = data[send:]

            while True:
                receive_data = sock.recv(1024)

                if receive_data:
                    print("Client #" + str(i) + " Reply: ", receive_data)
                    break
                else:
                    print("Client #" + str(i) + " Error!")

            print("Client #" + str(i) + " Disconnect")
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
    else:
        (requests, remaining) = divmod(number, concur)

        for i in range(0, number):
            if i == number - 1:
                client = Worker((address, port), requests + remaining, i)
            else:
                client = Worker((address, port), requests, i)
            client.start()


def main():
    number = 10
    concurrency = 1
    server_address = '127.0.0.1'
    server_port = 80
    request_path = "/"

    parser = optparse.OptionParser()

    parser.add_option("-n", "--number", help="Number of requests to perform",
                      type="int", dest="number")
    parser.add_option("-c", "--concurrency", help="Number of multiple requests to make at a time",
                      type="int", dest="concurrency")

    (options, args) = parser.parse_args()
    address = args[0]

    idx = address.find(":")
    if idx >= 0:
        server_address = address[:idx]

        idx2 = address.find("/")

        if idx2 >= 0:
            server_port = int(address[idx + 1:idx2])
            request_path = address[idx2:]
        else:
            server_port = int(address[idx + 1:])
    else:
        server_address = address

    if options.number is not None:
        number = options.number
    if options.concurrency is not None:
        concurrency = options.concurrency

    run_tests(server_address, server_port, request_path, number, concurrency)


if __name__ == "__main__":
    main()
