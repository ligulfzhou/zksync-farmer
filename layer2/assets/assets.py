import os
import json


def get_abi(abi_file: str):
    with open(os.path.join(os.path.dirname(__file__), abi_file)) as f:
        return json.loads(f.read())
