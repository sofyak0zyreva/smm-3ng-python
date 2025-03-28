import asn1tools
import socket
import struct

asn1_compiler = asn1tools.compile_files(["../smm3ng-types/smm3ng-types.asn1",
                                         "../smm3ng-protocol/smm3ng-protocol.asn1"], codec="der")


def sendPDU(sock, pdu):
    # print(f"pdu {pdu}")
    try:
        encoded_pdu = asn1_compiler.encode('SMM3NG-PDU', pdu)
    except Exception as e:
        raise RuntimeError("PDU encoding failed: {e}")
    pdu_length = len(encoded_pdu)
# Unlike send(), this method continues to send data from bytes until either all data has been sent or an error occurs.
# None is returned on success.
# The first character of the format string can be used to indicate the byte order, size and alignment of the packed data
# (network (= big-endian) standard size no alignment)
    try:
        sock.send(struct.pack("<I", pdu_length))
        # print(f"pdu_length {pdu_length}")
        sock.send(encoded_pdu)
    except (struct.error, socket.error) as e:
        raise RuntimeError(f"Failed to send PDU: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error while sending PDU: {e}")
    # print(f"encoded_pdu {encoded_pdu}")


def recvPDU(sock):
    pdu_length_data = sock.recv(4)
    # print(f"pdu_length_data ${pdu_length_data}")
    if not pdu_length_data:
        # print(f"Connection closed by peer")
        raise ValueError("Connection closed by peer")

    if len(pdu_length_data) != 4:
        raise RuntimeError(
            f"Invalid PDU length header (got {len(pdu_length_data)} bytes, expected 4)")
        # print(f"Cannot receive length of PDU: {len(pdu_length_data)}")
        # return None
    # The ‘Standard size’ column refers to the size of the packed value in bytes when using standard size
    # The result is a tuple even if it contains exactly one item
    pdu_length = struct.unpack("<I", pdu_length_data)[0]
    print(f"Received PDU length: {pdu_length}")
    # An empty bytes object
    pdu_data = b""
    while len(pdu_data) < pdu_length:
        chunk = sock.recv(pdu_length - len(pdu_data))
        if not chunk:
            raise RuntimeError(
                f"Connection closed before receiving full PDU (got {len(pdu_data)}/{pdu_length} bytes)")
        pdu_data += chunk
    print(f"Received PDU data: {pdu_data}")
    try:
        decoded_pdu = asn1_compiler.decode('SMM3NG-PDU', pdu_data)
    except Exception as e:
        raise RuntimeError("PDU decoding failed: {e}")
    print(f"decoded PDU data: {decoded_pdu}")
    return decoded_pdu
