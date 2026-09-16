import json


def load_abi(path: str) -> list:
    with open(path, "r") as f:
        data = json.load(f)

        return data["abi"]
