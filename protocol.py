import socket
import struct
import os
import asn1tools  # type: ignore

current_dir = os.path.dirname(os.path.abspath(__file__))
asn1_file_paths = [
    os.path.join(current_dir, "asn1", "types.asn1"),
    os.path.join(current_dir, "asn1", "protocol.asn1"),
]

asn1_compiler = asn1tools.compile_files(
    asn1_file_paths,
    codec="der",
)


def sendPDU(sock, pdu):
    try:
        encoded_pdu = asn1_compiler.encode("SMM3NG-PDU", pdu)
    except Exception as e:
        raise RuntimeError(f"PDU encoding failed: {e}")
    pdu_length = len(encoded_pdu)
    # Unlike send(), this method continues to send data from bytes until either
    # all data has been sent or an error occurs.
    # None is returned on success.
    # The first character of the format string can be used to indicate the
    # byte order, size and alignment of the packed data
    # (network (= big-endian) standard size no alignment)
    try:
        sock.send(struct.pack("<I", pdu_length))
        sock.send(encoded_pdu)
    except (struct.error, socket.error) as e:
        raise RuntimeError(f"Failed to send PDU: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error while sending PDU: {e}")


def recvPDU(sock):
    pdu_length_data = sock.recv(4)
    if not pdu_length_data:
        raise ValueError("Connection closed by peer")

    if len(pdu_length_data) != 4:
        raise RuntimeError(
            f"Invalid PDU length header (got {len(pdu_length_data)} bytes, expected 4)"
        )
    # The ‘Standard size’ column refers to the size of the packed value in
    # bytes when using standard size
    # The result is a tuple even if it contains exactly one item
    pdu_length = struct.unpack("<I", pdu_length_data)[0]
    print(f"Received PDU length: {pdu_length}")
    # An empty bytes object
    pdu_data = b""
    while len(pdu_data) < pdu_length:
        chunk = sock.recv(pdu_length - len(pdu_data))
        if not chunk:
            raise RuntimeError(
                f"Connection closed before receiving full PDU (got {len(pdu_data)}/{pdu_length} bytes)"
            )
        pdu_data += chunk
    print(f"Received PDU data: {pdu_data}")
    try:
        decoded_pdu = asn1_compiler.decode("SMM3NG-PDU", pdu_data)
    except Exception as e:
        raise RuntimeError(f"PDU decoding failed: {e}")
    print(f"decoded PDU data: {decoded_pdu}")
    return decoded_pdu


def sendAckPDU(sock):
    pdu = ("ack", None)
    return sendPDU(sock, pdu)


def sendNackPDU(sock, reason):
    pdu = ("nack", reason)
    return sendPDU(sock, pdu)


# check if status is ack or nack.


def recvStatusPDU(sock):
    decoded_pdu = recvPDU(sock)
    if decoded_pdu[0] == "ack":
        return (True, None)
    elif decoded_pdu[0] == "nack":
        return (False, decoded_pdu[1])
    else:
        raise ValueError("Received PDU is neither an ack nor a nack")


def sendRegPDU(sock, algoName, className, port):
    pdu = ("reg", {"algoName": algoName, "className": className, "port": port})
    sendPDU(sock, pdu)


def sendNextCycle(sock, timestamp):
    pdu = ("nextCycle", {"timestamp": timestamp})
    sendPDU(sock, pdu)


def sendShiftValuesPDU(sock):
    pdu = ("shiftValues", None)
    sendPDU(sock, pdu)


def sendDonePDU(sock):
    pdu = ("done", None)
    sendPDU(sock, pdu)
