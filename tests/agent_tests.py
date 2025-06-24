from unittest.mock import patch, MagicMock
from unittest.mock import mock_open, patch
from agent import print_conn_pdu
import unittest
from unittest.mock import MagicMock, mock_open, patch

from agent import (
    create_data_responder_socket,
    connect_to_core,
    connect_to_peer,
    print_conn_pdu,
    start_agent,
)


class TestAgentFunctions(unittest.TestCase):
    """
    test successfully creating a listening socket
    """

    @patch("socket.socket")
    # 'self' refers to the test case instance
    # 'mock_socket_class' is the mock for socket.socket
    def test_create_data_responder_socket(self, mock_socket_class):
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        sock = create_data_responder_socket()
        self.assertEqual(sock, mock_socket)
        mock_socket.bind.assert_called()
        mock_socket.listen.assert_called_with(5)

    @patch("socket.socket")
    def test_connect_to_core(self, mock_socket_class):
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        with patch("agent.sendRegPDU") as mock_sendRegPDU:
            sock = connect_to_core("Algo", "Class", "tcp://127.0.0.1:1234", 5678)
            self.assertEqual(sock, mock_socket)
            mock_socket.connect.assert_called_with(("127.0.0.1", 1234))
            mock_sendRegPDU.assert_called_with(mock_socket, "Algo", "Class", 5678)

    @patch("socket.socket")
    def test_connect_to_peer(self, mock_socket_class):
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        sock = connect_to_peer("127.0.0.1", 1234)
        self.assertEqual(sock, mock_socket)
        mock_socket.connect.assert_called_with(("127.0.0.1", 1234))

    """
	test writing the correct content to the expected file
	"""

    @patch("builtins.open", new_callable=mock_open)
    # 'mock_file' is the result of mock_open(), so f becomes mock_file()
    def test_print_conn_pdu(self, mock_file):
        algo_name = "TestAlgo"
        conn_pdu = {
            "pull": [
                {
                    "localParamName": "x",
                    "remoteAlgoName": "A1",
                    "remoteParamName": "y",
                    "address": "127.0.0.1",
                    "port": 1000,
                },
                {
                    "localParamName": "m",
                    "remoteAlgoName": "A2",
                    "remoteParamName": "n",
                    "address": "127.0.0.1",
                    "port": 1001,
                },
            ],
            "push": [
                {
                    "localParamName": "a",
                    "remoteAlgoName": "B1",
                    "remoteParamName": "b",
                    "address": "127.0.0.2",
                    "port": 2000,
                }
            ],
        }

        print_conn_pdu(algo_name, conn_pdu)
        # Check that the file was opened with the correct path and mode
        mock_file.assert_called_once_with(f"/tmp/{algo_name}", "w")

        handle = mock_file()
        expected_calls = [
            unittest.mock.call("pull:"),
            unittest.mock.call("x <- A1(y) at 127.0.0.1:1000"),
            unittest.mock.call("m <- A2(n) at 127.0.0.1:1001"),
            unittest.mock.call("push:"),
            unittest.mock.call("a <- B1(b) at 127.0.0.2:2000"),
        ]
        handle.write.assert_has_calls(expected_calls, any_order=False)


class TestStartAgent(unittest.TestCase):

    @patch("agent.print_conn_pdu")
    @patch("agent.create_algorithm_instance")
    @patch("agent.sendAckPDU")
    @patch("agent.recvPDU")
    @patch("agent.connect_to_peer")
    @patch("agent.connect_to_core")
    @patch("agent.create_data_responder_socket")
    def test_start_agent_done_cycle(
        self,
        mock_create_sock,
        mock_connect_core,
        mock_connect_peer,
        mock_recvPDU,
        mock_sendAck,
        mock_create_algo,
        mock_print_conn_pdu,
    ):

        # Mock sockets
        mock_sock = MagicMock()
        mock_create_sock.return_value = mock_sock
        mock_sock.getsockname.return_value = ("localhost", 1234)
        mock_control_sock = MagicMock()
        mock_connect_core.return_value = mock_control_sock

        # Mock algorithm instance
        mock_algo = MagicMock()
        mock_algo.run.return_value = {"x": 42}
        mock_create_algo.return_value = mock_algo

        # Set up PDUs
        conn_data = {"pull": [], "push": []}
        mock_recvPDU.side_effect = [
            ("setConn", conn_data),
            ("nextCycle", None),
            ("shiftValues", [{"value": "x"}]),
            ("done", None),
        ]

        start_agent("Algo", "Class", "tcp://localhost:9999")

        # Verify connections
        mock_connect_core.assert_called()
        mock_sendAck.assert_called()
        mock_algo.run.assert_called()

    @patch("agent.print_conn_pdu")
    @patch("agent.create_algorithm_instance")
    @patch("agent.sendAckPDU")
    @patch("agent.recvStatusPDU")
    @patch("agent.sendPDU")
    @patch("agent.recvPDU")
    @patch("agent.connect_to_peer")
    @patch("agent.connect_to_core")
    @patch("agent.create_data_responder_socket")
    def test_full_start_agent_flow(
        self,
        mock_create_data_responder_socket,
        mock_connect_to_core,
        mock_connect_to_peer,
        mock_recvPDU,
        mock_sendPDU,
        mock_recvStatusPDU,
        mock_sendAckPDU,
        mock_create_algorithm_instance,
        mock_print_conn_pdu,
    ):
        mock_data_sock = MagicMock()
        mock_data_sock.getsockname.return_value = ("127.0.0.1", 5000)
        mock_create_data_responder_socket.return_value = mock_data_sock

        mock_control_sock = MagicMock()
        mock_connect_to_core.return_value = mock_control_sock

        mock_peer_sock = MagicMock()
        mock_connect_to_peer.return_value = mock_peer_sock

        # Set up the connection PDU
        conn_pdu_data = {
            "pull": [
                {
                    "localParamName": "input_val",
                    "remoteAlgoName": "my_producer",
                    "remoteParamName": "data",
                    "address": "127.0.0.1",
                    "port": 5000,
                }
            ],
            "push": [],
        }

        # Mock the algorithm's behavior
        algo_instance = MagicMock()
        algo_instance.run.return_value = {}
        mock_create_algorithm_instance.return_value = algo_instance

        # Simulate recvPDU responses from core and peer
        mock_recvPDU.side_effect = [
            ("setConn", conn_pdu_data),
            ("nextCycle", {"timestamp": 0}),
            ("pullValuesRep", [{"name": "data", "value": ("integer", 0)}]),
            ("shiftValues", None),
            ("done", None),
        ]

        start_agent("TestAlgo", "TestClass", "tcp://localhost:1234")

        mock_connect_to_core.assert_called_once()
        mock_connect_to_peer.assert_called_with("127.0.0.1", 5000)
        mock_sendAckPDU.assert_called()
        mock_sendPDU.assert_any_call(mock_peer_sock, ("pullValuesReq", ["data"]))
        algo_instance.run.assert_called_with({"input_val": ("integer", 0)})

    @patch("agent.print_conn_pdu")
    @patch("agent.create_algorithm_instance")
    @patch("agent.sendAckPDU")
    @patch("agent.recvStatusPDU")
    @patch("agent.sendPDU")
    @patch("agent.recvPDU")
    @patch("agent.connect_to_peer")
    @patch("agent.connect_to_core")
    @patch("agent.create_data_responder_socket")
    def test_wrong_next_cycle_pdu(
        self,
        mock_create_data_responder_socket,
        mock_connect_to_core,
        mock_connect_to_peer,
        mock_recvPDU,
        mock_sendPDU,
        mock_recvStatusPDU,
        mock_sendAckPDU,
        mock_create_algorithm_instance,
        mock_print_conn_pdu,
    ):
        mock_data_sock = MagicMock()
        mock_data_sock.getsockname.return_value = ("127.0.0.1", 5000)
        mock_create_data_responder_socket.return_value = mock_data_sock

        mock_control_sock = MagicMock()
        mock_connect_to_core.return_value = mock_control_sock

        conn_pdu_data = {
            "pull": [
                {
                    "localParamName": "powpow",
                    "remoteAlgoName": "peer_agent",
                    "remoteParamName": "data",
                    "address": "127.0.0.1",
                    "port": 5001,
                }
            ],
            "push": [],
        }

        # recvPDU returns: "setConn" PDU, and invalid command instead of "nextCycle"
        mock_recvPDU.side_effect = [("setConn", conn_pdu_data), ("badCommand", None)]

        mock_algo = MagicMock()
        mock_create_algorithm_instance.return_value = mock_algo

        start_agent("BadAgent", "BadClass", "tcp://localhost:1234")

        # Should NOT have called algo.run at all
        mock_algo.run.assert_not_called()
        # Should have connected to peer anyway
        mock_connect_to_peer.assert_called_with("127.0.0.1", 5001)

    @patch("agent.print_conn_pdu")
    @patch("agent.create_algorithm_instance")
    @patch("agent.sendAckPDU")
    @patch("agent.recvStatusPDU")
    @patch("agent.sendPDU")
    @patch("agent.recvPDU")
    @patch("agent.connect_to_peer")
    @patch("agent.connect_to_core")
    @patch("agent.create_data_responder_socket")
    def test_wrong_shift_values_pdu(
        self,
        mock_create_data_responder_socket,
        mock_connect_to_core,
        mock_connect_to_peer,
        mock_recvPDU,
        mock_sendPDU,
        mock_recvStatusPDU,
        mock_sendAckPDU,
        mock_create_algorithm_instance,
        mock_print_conn_pdu,
    ):

        mock_data_sock = MagicMock()
        mock_data_sock.getsockname.return_value = ("127.0.0.1", 5000)
        mock_create_data_responder_socket.return_value = mock_data_sock

        mock_control_sock = MagicMock()
        mock_connect_to_core.return_value = mock_control_sock

        mock_peer_sock = MagicMock()
        mock_connect_to_peer.return_value = mock_peer_sock

        conn_pdu_data = {
            "pull": [
                {
                    "localParamName": "input_val",
                    "remoteAlgoName": "PeerA",
                    "remoteParamName": "remote_val",
                    "address": "127.0.0.1",
                    "port": 5000,
                }
            ],
            "push": [
                {
                    "localParamName": "output_val",
                    "remoteAlgoName": "PeerB",
                    "remoteParamName": "remote_val",
                    "address": "127.0.0.1",
                    "port": 5000,
                }
            ],
        }

        algo_instance = MagicMock()
        algo_instance.run.return_value = {"x": ("integer", 123)}
        mock_create_algorithm_instance.return_value = algo_instance

        mock_recvPDU.side_effect = [
            ("setConn", conn_pdu_data),
            ("nextCycle", {"timestamp": 0}),
            ("pullValuesRep", [{"name": "data", "value": ("integer", 0)}]),
            ("notShiftValues", None),
        ]

        start_agent("BrokenShiftAlgo", "AgentClass", "tcp://localhost:1234")

        # Should have exited on bad shiftValues
        mock_connect_to_core.assert_called_once()
        mock_connect_to_peer.assert_called_with("127.0.0.1", 5000)
        self.assertTrue(mock_sendAckPDU.call_count == 2)
        algo_instance.run.assert_called_with({"input_val": ("integer", 0)})
