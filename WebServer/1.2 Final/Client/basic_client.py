__author__ = 'Ivan Dortulov'

import socket
import errno

if __name__ == '__main__':
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect(("localhost", 27015))
    except socket.error as ex:
        print("[ERROR] Unable to connect!")
    else:
        client_socket.setblocking(False)

        request = "GET /very_small_file.txt HTTP/1.1\r\n\r\nGET /very_small_file.txt HTTP/1.1\r\n\r\n"
        while len(request) > 0:
            try:
                sent = client_socket.send(request.encode())
            except socket.error as ex:
                print("[ERROR] Error sending: " + str(ex.args[1]))
            else:
                request = request[sent:]

        while True:
            try:
                recv_data = client_socket.recv(128)
            except socket.error as ex:
                error = ex.args[0]

                if error == errno.EWOULDBLOCK or error == errno.EAGAIN:
                    continue
                else:
                    print("[ERROR] Error receiving: " + str(ex.args[1]))
            else:
                if recv_data:
                    print("recv: ", recv_data)
                else:
                    break

        try:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
        except socket.error as ex:
            print("[ERROR]Unable to close socket: " + str(ex.args[1]))