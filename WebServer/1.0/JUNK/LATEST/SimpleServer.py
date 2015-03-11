__author__ = 'Ivan Dortulov'

import socket

# Maximum size of the html header
MAX_HEADER_SIZE = 4096

# Server address, port and size of the data chunks to be received and send by the server
server_address = "localhost"
server_port = 27015
chunk_size = 1024

# Create the server socket, bind it and listen
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((server_address, server_port))
server_socket.listen(5)
print("Listening on ", (server_address, server_port))

# Server is running
running = True

while running:
    # Accept incoming connections
    (client_socket, client_address) = server_socket.accept()
    print("Accepted: ", client_address)

    input_buffer = b""

    # Receive data
    while True:
        receive_data = client_socket.recv(chunk_size)
        if len(receive_data) == 0:
            print("Nothing to receive from ", client_address)
            break
        else:
            input_buffer += receive_data
            print("Received: ", len(receive_data), "bytes:\n", receive_data)

            idx = input_buffer.find(b"\r\n")
            if idx >= 0:
                print("Message received from ", client_address)
                break
            elif len(input_buffer) > MAX_HEADER_SIZE:
                print("Message from ", client_address, "is to long!")
                break

    send_data = b"OK " + input_buffer
    print("Responding to ", client_address, " with ", send_data)

    # Reply
    while len(send_data) > 0:
        sent = client_socket.send(send_data)

        send_data = send_data[sent:]
        print("Sent ", sent, " bytes to ", client_address)

    # Close connection
    try:
        client_socket.shutdown(socket.SHUT_RDWR)
        client_socket.close()
    except socket.error as ex:
        print("Error occurred closing socket: ", ex)
    else:
        print("Closed ", client_address)

# Shutdown server
server_socket.shutdown(socket.SHUT_RDWR)
server_socket.close()