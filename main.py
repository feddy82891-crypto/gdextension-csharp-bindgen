from parser import ApiParser
from generator import CSharpBindingGenerator

from pathlib import Path

import sys
import json

def load_api(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)

def main():
    path_to_extension_api = Path("extension_api.json")

    if len(sys.argv) > 1:
        path_to_extension_api = Path(sys.argv[1])

    if not path_to_extension_api.exists():
        raise FileNotFoundError(
            f"Could not find the Extension API file: {path_to_extension_api}"
        )

    raw_api = load_api(path_to_extension_api)
    api = ApiParser().parse(raw_api)

    CSharpBindingGenerator(api).generate_classes()

if __name__ == "__main__":
    main()