import math
import random

from application import AnonymousTransmissionProgram

from squidasm.run.stack.config import StackNetworkConfig
from squidasm.run.stack.run import run

nodes = ["Alice", "Bob", "Charlie", "David"]

# import network configuration from file
cfg = StackNetworkConfig.from_file("config.yaml")

num_times = 10
num_repetitions = 3

message_length = 8
message = ""
for _ in range(message_length):
    message = message + str(random.randint(0, 1))

# Create instances of programs to run
alice_program = AnonymousTransmissionProgram(node_name="Alice", node_names=nodes, message=message, message_length=message_length, num_repetitions=num_repetitions)
bob_program = AnonymousTransmissionProgram(node_name="Bob", node_names=nodes, message_length=message_length, num_repetitions=num_repetitions)
charlie_program = AnonymousTransmissionProgram(node_name="Charlie", node_names=nodes, message_length=message_length, num_repetitions=num_repetitions)
david_program = AnonymousTransmissionProgram(node_name="David", node_names=nodes, message_length=message_length, num_repetitions=num_repetitions)

# Run the simulation. Programs argument is a mapping of network node labels to programs to run on that node
results = run(config=cfg, programs={"Alice": alice_program, "Bob": bob_program, "Charlie": charlie_program, "David": david_program}, num_times=num_times)

correct_transfer_counter = 0

for i in range(num_times):
    counter = 1
    for node in results:
        if node[i]["msg"] != message:
            counter = 0
    correct_transfer_counter = correct_transfer_counter + counter

print(f"Average success probability = {math.floor(100 * correct_transfer_counter / num_times)} %")

average_node_runtime = 0
for node in results:
    average_node_runtime = average_node_runtime + node[num_times - 1]["runtime"] * 1E-9 / 4

# We only count bits transferred in rounds where WHOLE message was correct.
# This is, of course, not the only way to do this but was not specified in the assignment.
average_transmission_speed = math.floor(correct_transfer_counter * message_length / average_node_runtime)
print(f"Average transmission speed = {average_transmission_speed} bits / sec.")
