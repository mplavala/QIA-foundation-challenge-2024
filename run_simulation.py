from application import AnonymousTransmissionProgram

from squidasm.run.stack.config import StackNetworkConfig
from squidasm.run.stack.run import run

import random

nodes = ["Alice", "Bob", "Charlie", "David"]

# import network configuration from file
cfg = StackNetworkConfig.from_file("config.yaml")

message_length = 8
message = ""
for _ in range(message_length):
    message = message + str(random.randint(0, 1))

# Create instances of programs to run
alice_program = AnonymousTransmissionProgram(node_name="Alice", node_names=nodes, message=message, message_length=message_length)
bob_program = AnonymousTransmissionProgram(node_name="Bob", node_names=nodes, message_length=message_length)
charlie_program = AnonymousTransmissionProgram(node_name="Charlie", node_names=nodes, message_length=message_length)
david_program = AnonymousTransmissionProgram(node_name="David", node_names=nodes, message_length=message_length)

# Run the simulation. Programs argument is a mapping of network node labels to programs to run on that node
run(config=cfg, programs={"Alice": alice_program, "Bob": bob_program,
                          "Charlie": charlie_program, "David": david_program}, num_times=1)
