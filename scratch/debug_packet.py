
import sys
import os
import json

# Add workspace root to sys.path
sys.path.append("g:/Live Task Review Agent - 2")

from evaluation_engine.review_packet_parser import review_packet_parser

res = review_packet_parser.enforce_packet_requirement(".")
print(json.dumps(res, indent=2, default=str))
