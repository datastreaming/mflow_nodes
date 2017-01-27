import logging
import sys
from argparse import ArgumentParser
from mflow_node.stream_node import start_node
from mflow_processor.lz4_compressor import LZ4CompressionProcessor

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger("mflow.mflow").setLevel(logging.ERROR)

parser = ArgumentParser()
parser.add_argument("listening_address", type=str, help="Listening address for mflow connection.\n"
                                                        "Example: tcp://127.0.0.1:40000")
parser.add_argument("forwarding_address", type=str, help="Forwarding address for mflow connection.\n"
                                                         "Example: tcp://127.0.0.1:40001")
parser.add_argument("--rest_port", type=int, default=8080, help="Port for web interface.")
parser.add_argument("--block_size", type=int, default=2048, help="LZ4 block size.")
input_args = parser.parse_args()

start_node(processor=LZ4CompressionProcessor(),
           processor_parameters={"forwarding_address": input_args.forwarding_address},
           listening_address=input_args.listening_address,
           control_port=input_args.rest_port)