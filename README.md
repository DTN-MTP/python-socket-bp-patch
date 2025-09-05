## Socket-bp-patch

(Work in Progress)

Importing this package will patch some methods of socket to provide bundle protocol support

Create a server
```bash
import socket_bp_patch
import socket

sock = socket.socket(socket_bp_patch.AF_BP, socket.SOCK_DGRAM, 1)

server_address = ("ipn:10.2", None)
sock.bind(server_address)

print("Server listening on {}:{}".format(*server_address))

while True:
    data, address = sock.recvfrom(1024)
    print("Received:", data.decode(), "from", address)
```

Create a client
```bash
import socket_bp_patch
import socket

sock = socket.socket(socket_bp_patch.AF_BP, socket.SOCK_DGRAM, 1)
client_address = ("ipn:30.2", None)
sock.bind(client_address)
server_address = ("ipn:10.2", None)

message = b'Hello, server!'
sock.sendto(message, server_address)

```
