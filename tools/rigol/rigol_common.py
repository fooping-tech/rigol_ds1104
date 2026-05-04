"""Shared helpers for RIGOL DS1104Z command-line tools."""

from __future__ import annotations

import argparse
import os


def add_ip_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--ip",
        default=None,
        help="Oscilloscope IPv4 address. If omitted, RIGOL_IP is used.",
    )


def resolve_ip(args: argparse.Namespace) -> str:
    ip = args.ip or os.environ.get("RIGOL_IP")
    if not ip:
        raise ValueError("Oscilloscope IP is required. Pass --ip <addr> or set RIGOL_IP.")
    return ip
