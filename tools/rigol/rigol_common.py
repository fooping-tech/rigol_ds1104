"""Shared helpers for RIGOL DS1104Z command-line tools."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Optional


DEFAULT_CONFIG = "config/rigol.env"


def add_config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        help=f"Local env file to load before reading RIGOL_IP. Default: {DEFAULT_CONFIG}",
    )


def add_ip_argument(parser: argparse.ArgumentParser) -> None:
    add_config_argument(parser)
    parser.add_argument(
        "--ip",
        default=None,
        help="Oscilloscope IPv4 address. If omitted, RIGOL_IP is read from --config or the environment.",
    )


def load_env_file(path_text: Optional[str]) -> None:
    if not path_text:
        return

    path = Path(path_text)
    if not path.exists():
        return

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            raise ValueError(f"Invalid config line {line_number} in {path}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if not key:
            raise ValueError(f"Invalid config line {line_number} in {path}: empty key")
        os.environ.setdefault(key, value)


def resolve_ip(args: argparse.Namespace) -> str:
    load_env_file(getattr(args, "config", DEFAULT_CONFIG))
    ip = args.ip or os.environ.get("RIGOL_IP")
    if not ip:
        raise ValueError(
            f"Oscilloscope IP is required. Pass --ip <addr>, set RIGOL_IP, "
            f"or create {DEFAULT_CONFIG} from config/rigol.example.env."
        )
    return ip
