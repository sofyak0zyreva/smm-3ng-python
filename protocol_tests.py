import socket
import struct
import unittest
from unittest.mock import MagicMock

from protocol import (
    asn1_compiler,
    recvPDU,
    recvStatusPDU,
    sendAckPDU,
    sendDonePDU,
    sendNackPDU,
    sendNextCycle,
    sendPDU,
    sendRegPDU,
    sendShiftValuesPDU,
)


class TestPDUSocketFunctions(unittest.TestCase):
    # A mock socket is used so that tests are fast, isolated, and do not depend on network
    # runs before evety single test: every test gets a fresh mock
    def setUp(self):
        self.mock_socket = MagicMock()

    """
    test successfully sending and receiving PDU
    """

    def test_send_and_recv_pdu(self):
        pdu = ("ack", None)
        sendPDU(self.mock_socket, pdu)
        encoded = asn1_compiler.encode("SMM3NG-PDU", pdu)
        # Mock recv responses before calling recvPDU
        self.mock_socket.recv.side_effect = [
            struct.pack("<I", len(encoded)),  # PDU length
            encoded,  # actual PDU data
        ]
        received_pdu = recvPDU(self.mock_socket)
        self.assertEqual(received_pdu, pdu)

    """
    tests raising Runtime Error when sending PDU
    """
    # If the socket fails when sending, sendPDU function raises a RuntimeError

    def test_send_with_socket_error(self):
        pdu = ("ack", None)
        # Whenever sendPDU calls sock.send(...), it will raise socket.error("Mock socket error")
        self.mock_socket.send.side_effect = socket.error("Mock socket error")
        with self.assertRaises(RuntimeError):
            sendPDU(self.mock_socket, pdu)

    def test_send_with_struct_error(self):
        pdu = ("ack", None)
        self.mock_socket.send.side_effect = struct.error("Mock socket error")
        with self.assertRaises(RuntimeError):
            sendPDU(self.mock_socket, pdu)

    def test_send_with_exception(self):
        pdu = ("ack", None)
        self.mock_socket.send.side_effect = Exception("Mock socket error")
        with self.assertRaises(RuntimeError):
            sendPDU(self.mock_socket, pdu)

    """
    tests raising Runtime Error when receiving PDU
    """

    def test_recv_with_closed_connection(self):
        self.mock_socket.recv.return_value = b""
        with self.assertRaises(ValueError):
            recvPDU(self.mock_socket)

    def test_recv_with_incomplete_length_header(self):
        self.mock_socket.recv.return_value = b"\x08\x00"
        with self.assertRaises(RuntimeError):
            recvPDU(self.mock_socket)

    def test_recv_partial_pdu_data(self):
        length = struct.pack("<I", 8)
        self.mock_socket.recv.side_effect = [
            length,
            b"abc",  # Partial data
            b"",  # Simulate socket closing
        ]
        with self.assertRaises(RuntimeError) as cm:
            recvPDU(self.mock_socket)
        self.assertIn("Connection closed before receiving full PDU", str(cm.exception))

    """
    tests sending and receiving status PDUs
    """

    def test_send_ack_pdu(self):
        sendAckPDU(self.mock_socket)
        self.mock_socket.send.assert_called()

    def test_send_nack_pdu(self):
        reason = "Invalid input"
        sendNackPDU(self.mock_socket, reason)
        self.mock_socket.send.assert_called()

    def test_recv_ack_pdu(self):
        pdu = ("ack", None)
        encoded = asn1_compiler.encode("SMM3NG-PDU", pdu)
        self.mock_socket.recv.side_effect = [
            struct.pack("<I", len(encoded)),
            encoded,
        ]
        status, reason = recvStatusPDU(self.mock_socket)
        self.assertTrue(status)
        self.assertIsNone(reason)

    def test_recv_nack_pdu(self):
        pdu = ("nack", "Invalid input")
        encoded = asn1_compiler.encode("SMM3NG-PDU", pdu)
        self.mock_socket.recv.side_effect = [
            struct.pack("<I", len(encoded)),
            encoded,
        ]
        status, reason = recvStatusPDU(self.mock_socket)
        self.assertFalse(status)
        self.assertEqual(reason, "Invalid input")

    def test_recv_non_status_pdu(self):
        pdu = ("done", None)
        encoded = asn1_compiler.encode("SMM3NG-PDU", pdu)
        self.mock_socket.recv.side_effect = [
            struct.pack("<I", len(encoded)),
            encoded,
        ]
        with self.assertRaises(ValueError):
            recvStatusPDU(self.mock_socket)

    """
    tests sending other PDUs 
    """

    def test_send_shift_values_pdu(self):
        sendShiftValuesPDU(self.mock_socket)
        self.mock_socket.send.assert_called()

    def test_send_done_pdu(self):
        sendDonePDU(self.mock_socket)
        self.mock_socket.send.assert_called()

    def test_send_reg_pdu(self):
        algo_name = "Algo1"
        class_name = "ClassA"
        port = 8080
        sendRegPDU(self.mock_socket, algo_name, class_name, port)
        self.mock_socket.send.assert_called()

    def test_send_next_cycle_pdu(self):
        timestamp = 1234567890
        sendNextCycle(self.mock_socket, timestamp)
        self.mock_socket.send.assert_called()
