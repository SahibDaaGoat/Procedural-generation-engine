"""Headless generator bundled with the Windows Unity showcase."""

import json
from pathlib import Path
import sys

from web_server import generate_from_payload
from floor_diagrams import write_floor_diagrams


def main(request_path, output_path):
    output = Path(output_path)
    try:
        payload = json.loads(Path(request_path).read_text(encoding="utf-8-sig"))
        result = generate_from_payload(payload)
        write_floor_diagrams(result, output)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except Exception as error:
        output.write_text(json.dumps({"error": str(error)}), encoding="utf-8")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
