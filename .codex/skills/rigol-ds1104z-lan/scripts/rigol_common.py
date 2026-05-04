"""Shared helpers for RIGOL DS1104Z command-line tools."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Optional


DEFAULT_CONFIG = "config/rigol.env"
USER_CONFIG = "~/.config/rigol-ds1104z-lan/rigol.env"
SKILL_CONFIG = "config/rigol.env"


def add_config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        default=None,
        help=(
            "Local env file to read before shell RIGOL_IP. If omitted, tries "
            f"{DEFAULT_CONFIG}, {USER_CONFIG}, and the Skill-local {SKILL_CONFIG}."
        ),
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


def read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
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
        values[key] = value
    return values


def skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def default_config_candidates() -> list[Path]:
    return [
        Path(DEFAULT_CONFIG),
        Path(USER_CONFIG).expanduser(),
        skill_dir() / SKILL_CONFIG,
    ]


def read_config_ip(config_arg: Optional[str]) -> Optional[str]:
    if config_arg:
        return read_env_file(Path(config_arg).expanduser()).get("RIGOL_IP")

    for path in default_config_candidates():
        values = read_env_file(path)
        if values.get("RIGOL_IP"):
            return values["RIGOL_IP"]
    return None


def resolve_ip(args: argparse.Namespace) -> str:
    config_arg = getattr(args, "config", None)
    config_ip = read_config_ip(config_arg)
    ip = args.ip or config_ip or os.environ.get("RIGOL_IP")
    if not ip:
        candidates = ", ".join(str(path) for path in default_config_candidates())
        raise ValueError(
            f"Oscilloscope IP is required. Pass --ip <addr>, set RIGOL_IP, "
            f"or create one of these config files: {candidates}."
        )
    return ip
