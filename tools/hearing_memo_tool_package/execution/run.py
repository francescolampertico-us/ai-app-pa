#!/usr/bin/env python3
"""Convenience entrypoint for the Hearing Memo Generator."""
import os
import sys

# Ensure tool package root is on path
TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOL_ROOT not in sys.path:
    sys.path.insert(0, TOOL_ROOT)

from src.main import main

if __name__ == "__main__":
    main()
