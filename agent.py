import socket
import re
from protocol import *


def create_data_responder_socket():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to any available port and IP address
        sock.bind(("0.0.0.0", 0))
        sock.listen(5)
        print(f"Socket is listening on {sock.getsockname()}")
        return sock
    except socket.error as e:
        print(f"Error creating or binding socket: {e}")


def connect_to_core(algoName, className, url, data_port):
    # "." Matches any character except a newline
    # "+" Matches 1 or more (greedy) repetitions of the preceding RE
    #  \d Matches any decimal digit; equivalent to the set [0-9] in
    # bytes patterns or string patterns with the ASCII flag.
    # In string patterns without the ASCII flag, it will match the whole
    # range of Unicode digits.
    match = re.match(r"tcp://(\d+\.\d+\.\d+\.\d+):(\d+)", url)
    if not match:
        raise ValueError("Incorrect url format url" + url)
    host, port = match.groups()
    port = int(port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        print(f"Connected to {host}:{port}")
        print(f"sending reg pdu")
        sendRegPDU(sock, algoName, className, data_port)
        return sock

    except Exception as e:
        print(f"Error while connecting: {e}")
        raise
