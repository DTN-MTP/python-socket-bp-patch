import socket_bp_patch
import socket

sock = socket.socket(socket_bp_patch.AF_BP, socket.SOCK_DGRAM, 1)
client_address = ("ipn:30.2", None)
sock.bind(client_address)
server_address = ("ipn:10.2", None)

message = b'Hello, server!'
sock.sendto(message, server_address)
