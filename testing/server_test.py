from threading import *
from socket import *

server = socket(AF_INET, SOCK_STREAM)
Port = 34000

Host = "127.0.0.1"
BufferSize = 2048
server.bind((Host, Port))
server.listen(1000)

while True:
    connection, address = server.accept()
    print("Accepted connection")

    while True:
        response = connection.recv(BufferSize).decode("utf8")
        print(str(response))

def listen(id, server):
    while True:
        client_connection, client_address = server.accept()
        request_data = client_connection.recv(1024)
        executeCommand(id)

        http_response = b"""\
    HTTP/1.1 200 OK
    """
        client_connection.sendall(http_response)
        client_connection.close()

        print(str(id))