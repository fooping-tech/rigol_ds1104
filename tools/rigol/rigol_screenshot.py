#!/usr/bin/env python3
"""Capture a DS1104Z screenshot over LAN."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import pyvisa


DEFAULT_TIMEOUT_MS = 15000


def timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


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


def read_ieee_block(scope: Any, command: str) -> bytes:
    scope.write(command)
    raw = bytes(scope.read_raw())
    if not raw.startswith(b"#"):
        raise RuntimeError(f"{command} did not return an IEEE binary block; first bytes={raw[:16]!r}")

    if len(raw) < 2 or not chr(raw[1]).isdigit():
        raise RuntimeError(f"{command} returned an invalid IEEE block header: {raw[:16]!r}")

    digits = int(chr(raw[1]))
    if digits <= 0:
        raise RuntimeError(f"{command} returned unsupported indefinite-length block")

    header_len = 2 + digits
    while len(raw) < header_len:
        raw += bytes(scope.read_raw())

    payload_len = int(raw[2:header_len].decode("ascii"))
    total_len = header_len + payload_len
    while len(raw) < total_len:
        raw += bytes(scope.read_raw())

    return raw[header_len:total_len]


def capture_screenshot(ip: str, socket: bool, outdir: Path, timeout_ms: int) -> Path:
    rm, scope, resource = open_scope(ip, socket, timeout_ms)
    try:
        idn = str(scope.query("*IDN?")).strip()
        print(f"*IDN?: {idn}")
        png = read_ieee_block(scope, ":DISP:DATA? PNG")
        if not png.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("Screenshot payload was received but does not look like a PNG file")

        outdir.mkdir(parents=True, exist_ok=True)
        base = f"rigol_screenshot_{timestamp()}"
        png_path = outdir / f"{base}.png"
        json_path = outdir / f"{base}.json"
        png_path.write_bytes(png)
        json_path.write_text(
            json.dumps(
                {
                    "idn": idn,
                    "resource": resource,
                    "command": ":DISP:DATA? PNG",
                    "screenshot_png": str(png_path),
                    "timestamp": base.removeprefix("rigol_screenshot_"),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return png_path
    finally:
        try:
            scope.close()
        finally:
            rm.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture a DS1104Z screenshot as PNG.")
    parser.add_argument("--ip", required=True, help="Oscilloscope IPv4 address")
    parser.add_argument("--socket", action="store_true", help="Use TCPIP0::<IP>::5555::SOCKET instead of INSTR")
    parser.add_argument("--outdir", default="captures", help="Output directory")
    parser.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS, help="VISA timeout in milliseconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        path = capture_screenshot(args.ip, args.socket, Path(args.outdir), args.timeout_ms)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Failed to capture screenshot: {exc}", file=sys.stderr)
        return 1

    print(f"Saved screenshot: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
