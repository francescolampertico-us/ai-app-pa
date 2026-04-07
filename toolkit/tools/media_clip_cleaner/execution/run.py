#!/usr/bin/env python3
"""CLI entry point for the Media Clip Cleaner.

Delegates to clean_clip.main() which owns the full argparse interface.

Usage:
    python3 run.py --input-file article.txt --output-file cleaned.txt
    python3 run.py --raw-text "Paste article text here..."
    python3 run.py --help
"""
import os
import sys

EXEC_DIR = os.path.dirname(os.path.abspath(__file__))
if EXEC_DIR not in sys.path:
    sys.path.insert(0, EXEC_DIR)

from clean_clip import main

if __name__ == "__main__":
    main()
