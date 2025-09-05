"""Init."""

import re
import socket
import ctypes
import os

# https://github.com/DTN-MTP/bp-socket/blob/main/include/bp_socket.h

AF_BP = 28
BP_SCHEME_IPN = 1


class SockaddrBP_IPN(ctypes.Structure):
    _fields_ = [
        ("node_id", ctypes.c_uint32),
        ("service_id", ctypes.c_uint32),
    ]

class SockaddrBP_Addr(ctypes.Union):
    _fields_ = [
        ("ipn", SockaddrBP_IPN)
    ]


class SockaddrBP(ctypes.Structure):
    _fields_ = [
        ("bp_family", ctypes.c_ushort),
        ("_pad1", ctypes.c_ushort),       # 2 bytes padding
        ("bp_scheme", ctypes.c_ushort),
        ("_pad2", ctypes.c_ushort),       # 2 bytes padding to align bp_addr
        ("bp_addr", SockaddrBP_Addr)
    ]

# ---- libc.bind() setup ----
libc = ctypes.CDLL("libc.so.6", use_errno=True)

_bind = libc.bind
_bind.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
_bind.restype = ctypes.c_int

_libc_sendto = libc.sendto
_libc_sendto.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t,
                         ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
_libc_sendto.restype = ctypes.c_ssize_t

_libc_recvfrom = ctypes.CDLL("libc.so.6", use_errno=True).recvfrom
_libc_recvfrom.argtypes = [
    ctypes.c_int,       # fd
    ctypes.c_void_p,    # buffer
    ctypes.c_size_t,    # length
    ctypes.c_int,       # flags
    ctypes.c_void_p,    # sockaddr
    ctypes.POINTER(ctypes.c_uint32)  # sockaddr length
]
_libc_recvfrom.restype = ctypes.c_ssize_t


# Keep reference to original bind
_original_bind = socket.socket.bind
_original_init = socket.socket.__init__
_original_sendto = socket.socket.sendto
_original_recvfrom = socket.socket.recvfrom

def parse_ipn(s: str):
    match = re.match(r"^ipn:(\d+).(\d+)$", s)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


# TODO: Lazy init ? most high level lib don't specify the address family directly
def patched_init(self, family=-1, type=-1, proto=-1, fileno=None):

    if(family == AF_BP):
        proto = 1
    _original_init(self, family, type, proto, fileno)

# For BP, address = (eid, _unused)
def patched_bind(self, address):
    host, _port = address
    print(host, _port)
    dtn_parsed = parse_ipn(host)
    if dtn_parsed is None:
        return _original_bind(self, address)

    node, service = dtn_parsed
    sa = SockaddrBP()
    sa.bp_family = AF_BP
    sa.bp_scheme = BP_SCHEME_IPN
    sa.bp_addr.ipn.node_id = node
    sa.bp_addr.ipn.service_id = service

    fd = self.fileno()
    res = _bind(fd, ctypes.byref(sa), ctypes.sizeof(sa))
    if res != 0:
        err = ctypes.get_errno()
        raise OSError(err, f"bind failed: {os.strerror(err)}")
    return res

def patched_sendto(self, data, address):
    host, port = address
    dtn_parsed = parse_ipn(host)

    if dtn_parsed is None:
        return _original_sendto(self, data, address)

    node, service = dtn_parsed
    sa = SockaddrBP()
    sa.bp_family = AF_BP
    sa.bp_scheme = BP_SCHEME_IPN
    sa.bp_addr.ipn.node_id = node
    sa.bp_addr.ipn.service_id = service

    fd = self.fileno()
    buf = ctypes.create_string_buffer(data)
    res = _libc_sendto(fd, buf, len(data), 0, ctypes.byref(sa), ctypes.sizeof(sa))
    if res < 0:
        err = ctypes.get_errno()
        raise OSError(err, f"sendto failed: {os.strerror(err)}")
    return res



def patched_recvfrom(self, bufsize, flags=0):
    if self.family != 28:  # AF_BP
        return _original_recvfrom(bufsize, flags)

    buf = ctypes.create_string_buffer(bufsize)
    sa = SockaddrBP()
    sa_len = ctypes.c_uint32(ctypes.sizeof(sa))

    fd = self.fileno()
    res = _libc_recvfrom(fd, buf, bufsize, flags, ctypes.byref(sa), ctypes.byref(sa_len))
    if res < 0:
        err = ctypes.get_errno()
        raise OSError(err, f"recvfrom failed: {os.strerror(err)}")

    data = buf.raw[:res]

    # Return Python-style (ipn:<node>.<service>, None)
    address = (f"ipn:{sa.bp_addr.ipn.node_id}.{sa.bp_addr.ipn.service_id}", None)
    return data, address


# Patch the socket class
socket.socket.__init__ = patched_init
socket.socket.bind = patched_bind
socket.socket.sendto = patched_sendto
socket.socket.recvfrom = patched_recvfrom