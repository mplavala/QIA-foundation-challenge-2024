from copy import copy
from typing import Optional, Generator

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta
from netqasm.sdk.classical_communication.socket import Socket
from netqasm.sdk.epr_socket import EPRSocket


class AnonymousTransmissionProgram(Program):
    def __init__(self, node_name: str, node_names: list, send_bit: bool = None):
        """
        Initializes the AnonymousTransmissionProgram.

        :param node_name: Name of the current node.
        :param node_names: List of all node names in the network, in sequence.
        :param send_bit: The bit to be transmitted; set to None for nodes that are not the sender.
        """
        self.node_name = node_name
        self.send_bit = send_bit

        # Find what nodes are upstream and downstream based on the node_names list
        node_index = node_names.index(node_name)
        self.upstream_node_name = node_names[node_index+1] if node_index + 1 < len(node_names) else None
        self.downstream_node_name = node_names[node_index-1] if node_index - 1 >= 0 else None

        # The remote nodes are all the nodes, but without current node. Copy the list to make the pop operation local
        self.remote_node_names = copy(node_names)
        self.remote_node_names.pop(node_index)

        # Upstream and downstream sockets, will be fetched from the ProgramContext using setup_up_and_downstream_sockets
        self.up_socket: Optional[Socket] = None
        self.up_epr_socket: Optional[EPRSocket] = None
        self.down_socket: Optional[Socket] = None
        self.down_epr_socket: Optional[EPRSocket] = None

    @property
    def meta(self) -> ProgramMeta:
        # Filter upstream and downstream node name for None values
        epr_node_names = [node for node in [self.upstream_node_name, self.downstream_node_name] if node is not None]

        return ProgramMeta(
            name="anonymous_transmission_program",
            csockets=self.remote_node_names,
            epr_sockets=epr_node_names,
            max_qubits=2,
        )

    def run(self, context: ProgramContext):
        # Initialize upstream and downstream sockets using the provided context
        self.setup_up_and_downstream_sockets(context)

        # Run the anonymous transmission protocol and retrieve the received bit
        received_bit = yield from self.anonymous_transmit_bit(context, self.send_bit)

        print(f"{self.node_name} has received the bit: {received_bit}")
        return {}

    def anonymous_transmit_bit(self, context: ProgramContext, send_bit: bool = None) -> Generator[None, None, bool]:
        """
        Anonymously transmits a bit to other nodes in the network as part of the protocol.

        :param context: The program's execution context.
        :param send_bit: Bit to be sent by the sender node; receivers should leave this as None.
        :return: The bit received through the protocol, or the sent bit if this node is the sender.
        """
        # Placeholder for the anonymous transmission protocol logic, put your code here.
        # This code makes the current code runnable; replace it with your actual protocol steps.
        yield from context.connection.flush()
        return False

    def broadcast_message(self, context: ProgramContext, message: str):
        """Broadcasts a message to all nodes in the network except the sender."""
        for remote_node_name in self.remote_node_names:
            socket = context.csockets[remote_node_name]
            socket.send(message)

    def setup_up_and_downstream_sockets(self, context: ProgramContext):
        """Initializes upstream and downstream socket properties using the given context."""
        if self.upstream_node_name:
            self.up_socket = context.csockets[self.upstream_node_name]
            self.up_epr_socket = context.epr_sockets[self.upstream_node_name]
        if self.downstream_node_name:
            self.down_socket = context.csockets[self.downstream_node_name]
            self.down_epr_socket = context.epr_sockets[self.downstream_node_name]
