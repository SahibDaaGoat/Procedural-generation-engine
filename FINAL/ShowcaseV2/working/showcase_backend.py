"""Root entry point for the packaged Unity generator worker."""

import sys

from json_handoff.showcase_backend import main


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
