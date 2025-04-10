import select
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


def connect_to_peer(addr, data_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((addr, data_port))
        return sock
    except OSError as e:
        print(f"Error while connecting: {e}")

# conn_pdu = {"push" : [{"localParamName": , "remoteAlgoName": , "remoteParamName": , "address": , "port" : }, {}, ..],
# "pull" : [{}, {}, ..]}


def print_conn_pdu(algoName, conn_pdu):
    file_path = f"/tmp/{algoName}"
    # the with statement automatically closes the file when the block ends
    with open(file_path, "w") as f:
        print(f"Temporary file created at: {f.name}")
        f.write(f"pull:")
        for c in (conn_pdu["pull"]):
            f.write(
                f'{c["localParamName"]} <- {c["remoteAlgoName"]}({c["remoteParamName"]}) at {c["address"]}:{c["port"]}')
        f.write(f"push:")
        for c in (conn_pdu["push"]):
            f.write(
                f'{c["localParamName"]} <- {c["remoteAlgoName"]}({c["remoteParamName"]}) at {c["address"]}:{c["port"]}')


# pullValuesReq = ["", "", ..]
# SMM3NG-Variable = {"name": "<..>", "value": ("<..>", <..>)}
# PullValuesRepPDU = [SMM3NG-Variable, SMM3NG-Variable, ..]
output_params = {}
input_params = {}   # Stores received values


def data_responder_proc(sock):
    peers = [sock]
    while True:
        read_fds = peers.copy()
        # для мультиплексирования сокетов
        try:
            readable, _, _ = select.select(read_fds, [], [])
        except (ValueError, OSError) as e:
            print(f"Select error: {e}")
        for s in readable:
            if s == sock:
                try:
                    conn, _ = sock.accept()
                    peers.append(conn)
                except OSError as e:
                    print(f"Accept failed: {e}")
            else:
                try:
                    pdu = recvPDU(s)
                except (ValueError, RuntimeError) as e:
                    print(f"Cannot receive data from agent peer: {e}")
                    return

                try:
                    # handling error in reception??
                    if pdu[0] == "pullValuesReq":
                        reply = []
                        for param_name in (pdu[1]):
                            if param_name in output_params:
                                var = {"name": param_name,
                                       "value": output_params[param_name]}
                            reply.append(var)
                        sendPDU(s, ("pullValuesRep", reply))
                    elif pdu[0] == "pushValues":
                        for var in pdu[1]:
                            param_name = var["name"]
                            input_params[param_name] = var["value"]
                        sendAckPDU(s)
                    else:
                        print(f"Invalid PDU received from agent peer")
                        return
                except (RuntimeError, OSError, struct.error, ValueError) as e:
                    print(f"Cannot send PDU to agent peer: {e}")
                    # peers.remove(s)
                    # s.close()

# toy start_agent
def start_agent(algoName, className, url):
    # Create a socket for receiving data from other agents
    data_responder_socket = create_data_responder_socket()
    # Get the assigned port
    port = data_responder_socket.getsockname()[1]
    try:
        control_socket = connect_to_core(algoName, className, url, port)
        print(f"control_socket ${control_socket}")
    except Exception as e:
        print(f"Error occured: {e}")
        return control_socket
