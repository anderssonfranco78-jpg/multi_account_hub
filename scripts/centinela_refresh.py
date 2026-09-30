#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centinela Refresh Runner — Multi-Account Hub
=============================================
Automated script for Cloud Centinela (GitHub Actions at 12:00 UTC / 06:00 AM CST).
Safely polls live metrics for active stores and respects the Visual Inmutability Shield (§ 7).

Usage:
    python scripts/centinela_refresh.py
    python scripts/centinela_refresh.py --all
"""

import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from hub_engine import cli_main


def main() -> int:
    """Invokes hub_engine refresh for all active businesses."""
    args = sys.argv[1:]
    if not args:
        args = ["refresh", "--all"]
    elif "refresh" not in args and not any(a.startswith("--refresh") for a in args):
        args = ["refresh"] + args

    return cli_main(args)


if __name__ == "__main__":
    sys.exit(main())
