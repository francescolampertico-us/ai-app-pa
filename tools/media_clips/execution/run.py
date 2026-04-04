#!/usr/bin/env python3
"""CLI entry point for the Media Clips Generator.

Delegates to generate_clips.main() which owns the full argparse interface.

Usage:
    python3 run.py --topic "India Media Clips" --queries '"India","Modi"' --period 24h
    python3 run.py --help
"""
import os
import sys

EXEC_DIR = os.path.dirname(os.path.abspath(__file__))
if EXEC_DIR not in sys.path:
    sys.path.insert(0, EXEC_DIR)

from generate_clips import main

if __name__ == "__main__":
    main()
