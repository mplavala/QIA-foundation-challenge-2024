from copy import copy
from typing import Optional, Generator

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta
from squidasm.util.routines import create_ghz
from netsquid.util.simtools import sim_time
from netqasm.sdk.classical_communication.socket import Socket
from netqasm.sdk.epr_socket import EPRSocket

from utils import hamming_weight


class AnonymousTransmissionProgram(Program):
    def __init__(self,
                 node_name: str,
                 node_names: list,
                 message: str = None,
                 message_length: int = 1,
                 num_repetitions: int = 1):
        """
        Initializes the AnonymousTransmissionProgram.

        :param node_name: Name of the current node.
        :param node_names: List of all node names in the network, in sequence.
        :param send_bit: The bit to be transmitted; set to None for nodes that are not the sender.
        """
        self.node_name = node_name
        self.message = message
        self.message_length = message_length
        self.num_repetitions = num_repetitions

        # Find what nodes are next and prev based on the node_names list
        node_index = node_names.index(node_name)
        self.next_node_name = node_names[node_index+1] if node_index + 1 < len(node_names) else None
        self.prev_node_name = node_names[node_index-1] if node_index - 1 >= 0 else None

        # The remote nodes are all the nodes, but without current node. Copy the list to make the pop operation local
        self.remote_node_names = copy(node_names)
        self.remote_node_names.pop(node_index)

        # next and prev sockets, will be fetched from the ProgramContext using setup_next_and_prev_sockets
        self.next_socket: Optional[Socket] = None
        self.next_epr_socket: Optional[EPRSocket] = None
        self.prev_socket: Optional[Socket] = None
        self.prev_epr_socket: Optional[EPRSocket] = None

    @property
    def meta(self) -> ProgramMeta:
        # Filter next and prev node name for None values
        epr_node_names = [node for node in [self.next_node_name, self.prev_node_name] if node is not None]

        return ProgramMeta(
            name="anonymous_transmission_program",
            csockets=self.remote_node_names,
            epr_sockets=epr_node_names,
            max_qubits=2,
        )

    def run(self, context: ProgramContext):
        # Initialize next and prev sockets using the provided context
        self.setup_next_and_prev_sockets(context)

        received_message = ""

        for i in range(self.message_length):
            if self.message is not None:
                send_bit = bool(int(self.message[i]))
            else:
                send_bit = None
            # Run the anonymous transmission protocol and retrieve the received bits
            received_bits = ""
            for ii in range(self.num_repetitions):
                received_bit = yield from self.anonymous_transmit_bit(context, send_bit)
                received_bits = received_bits + str(int(received_bit))

            # Error correction
            if hamming_weight(received_bits) > self.num_repetitions / 2:
                corrected_bit = 1
            else:
                corrected_bit = 0

            received_message = received_message + str(int(corrected_bit))

        # print(f"{self.node_name} has received the bit: {received_message}")
        return {"msg": received_message, "runtime": sim_time()}

    def anonymous_transmit_bit(self, context: ProgramContext, send_bit: bool = None) -> Generator[None, None, bool]:
        """
        Anonymously transmits a bit to other nodes in the network as part of the protocol.

        :param context: The program's execution context.
        :param send_bit: Bit to be sent by the sender node; receivers should leave this as None.
        :return: The bit received through the protocol, or the sent bit if this node is the sender.
        """

        qubit, m_ghz = yield from create_ghz(context.connection,
                                             self.prev_epr_socket,
                                             self.next_epr_socket,
                                             self.prev_socket,
                                             self.next_socket,
                                             True)

        if send_bit == 1:
            qubit.Z()

        qubit.H()
        m = qubit.measure()

        yield from context.connection.flush()

        self.broadcast_message(context, str(int(m)))

        yield from context.connection.flush()

        meas_string = str(int(m))
        for remote_node_name in self.remote_node_names:
            socket = context.csockets[remote_node_name]
            msg = yield from socket.recv()
            meas_string = meas_string + msg

        sent_bit = hamming_weight(meas_string) % 2

        return bool(sent_bit)

    def broadcast_message(self, context: ProgramContext, message: str):
        """Broadcasts a message to all nodes in the network."""
        for remote_node_name in self.remote_node_names:
            socket = context.csockets[remote_node_name]
            socket.send(message)

    def setup_next_and_prev_sockets(self, context: ProgramContext):
        """Initializes next and prev sockets using the given context."""
        if self.next_node_name:
            self.next_socket = context.csockets[self.next_node_name]
            self.next_epr_socket = context.epr_sockets[self.next_node_name]
        if self.prev_node_name:
            self.prev_socket = context.csockets[self.prev_node_name]
            self.prev_epr_socket = context.epr_sockets[self.prev_node_name]
