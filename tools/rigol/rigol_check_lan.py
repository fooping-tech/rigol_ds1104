#!/usr/bin/env python3
"""Check LAN connectivity to a RIGOL DS1104Z with *IDN?."""

from __future__ import annotations

import argparse
import sys
from typing import Any

import pyvisa


DEFAULT_TIMEOUT_MS = 5000


def resource_string(ip: str, socket: bool) -> str:
    if socket:
        return f"TCPIP0::{ip}::5555::SOCKET"
    return f"TCPIP0::{ip}::INSTR"


def open_scope(ip: str, socket: bool, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> tuple[Any, Any, str]:
    resource = resource_string(ip, socket)
    rm = pyvisa.ResourceManager("@py")
    scope = rm.open_resource(resource)
    scope.timeout = timeout_ms
    if socket:
        scope.write_termination = "\n"
        scope.read_termination = "\n"
    return rm, scope, resource


def query_idn(ip: str, socket: bool, timeout_ms: int) -> str:
    rm, scope, resource = open_scope(ip, socket, timeout_ms)
    try:
        print(f"Resource: {resource}")
        print(f"Timeout: {timeout_ms} ms")
        return str(scope.query("*IDN?")).strip()
    finally:
        try:
            scope.close()
        finally:
            rm.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check DS1104Z LAN connection with *IDN?.")
    parser.add_argument("--ip", required=True, help="Oscilloscope IPv4 address, e.g. 192.168.1.100")
    parser.add_argument("--socket", action="store_true", help="Use TCPIP0::<IP>::5555::SOCKET instead of INSTR")
    parser.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS, help="VISA timeout in milliseconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        idn = query_idn(args.ip, args.socket, args.timeout_ms)
    except Exception as exc:  # noqa: BLE001 - CLI should show actionable context.
        mode = "SOCKET" if args.socket else "INSTR"
        print(f"ERROR: Failed to query *IDN? using {mode} mode for {args.ip}: {exc}", file=sys.stderr)
        return 1

    print(f"*IDN?: {idn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
