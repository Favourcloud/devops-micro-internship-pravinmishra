#!/usr/bin/env python3
"""Public-source verifier; implementation is shared with the future runtime."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))
from upstream import main

if __name__ == "__main__":
    sys.exit(main())
