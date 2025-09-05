import socket_bp_patch
import socket

sock = socket.socket(socket_bp_patch.AF_BP, socket.SOCK_DGRAM, 1)

server_address = ("ipn:10.2", None)
sock.bind(server_address)

print("Server listening on {}:{}".format(*server_address))

while True:
    data, address = sock.recvfrom(1024)
    print("Received:", data.decode(), "from", address)