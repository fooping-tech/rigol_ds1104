#!/usr/bin/env python3
"""Export a DS1104Z displayed waveform to CSV using :WAV:PRE? scaling."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Union

import pyvisa


DEFAULT_TIMEOUT_MS = 15000
PREAMBLE_KEYS = [
    "format",
    "type",
    "points",
    "count",
    "xincrement",
    "xorigin",
    "xreference",
    "yincrement",
    "yorigin",
    "yreference",
]


def timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def normalize_channel(channel: str) -> str:
    value = channel.upper()
    if value in {"1", "2", "3", "4"}:
        value = f"CHAN{value}"
    if value not in {"CHAN1", "CHAN2", "CHAN3", "CHAN4"}:
        raise ValueError("channel must be CHAN1, CHAN2, CHAN3, CHAN4, or 1-4")
    return value


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


def parse_preamble(text: str) -> dict[str, Union[float, int]]:
    parts = [part.strip() for part in text.strip().split(",")]
    if len(parts) < len(PREAMBLE_KEYS):
        raise ValueError(f"Unexpected :WAV:PRE? format: expected at least 10 fields, got {len(parts)}: {text!r}")

    parsed: dict[str, Union[float, int]] = {}
    for key, value in zip(PREAMBLE_KEYS, parts):
        if key in {"format", "type", "points", "count"}:
            parsed[key] = int(float(value))
        else:
            parsed[key] = float(value)
    return parsed


def convert_sample(index: int, adc: int, preamble: dict[str, Union[float, int]]) -> tuple[float, float]:
    xincrement = float(preamble["xincrement"])
    xorigin = float(preamble["xorigin"])
    xreference = float(preamble["xreference"])
    yincrement = float(preamble["yincrement"])
    yorigin = float(preamble["yorigin"])
    yreference = float(preamble["yreference"])

    time_s = (index - xreference) * xincrement + xorigin
    voltage_v = (adc - yorigin - yreference) * yincrement
    return time_s, voltage_v


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


def export_waveform(args: argparse.Namespace) -> tuple[Path, Path]:
    channel = normalize_channel(args.channel)
    outdir = Path(args.outdir)
    rm, scope, resource = open_scope(args.ip, args.socket, args.timeout_ms)
    try:
        idn = str(scope.query("*IDN?")).strip()
        print(f"*IDN?: {idn}")

        scope.write(":STOP")
        scope.write(f":WAV:SOUR {channel}")
        scope.write(":WAV:MODE NORM")
        scope.write(":WAV:FORM BYTE")
        preamble_text = str(scope.query(":WAV:PRE?")).strip()
        preamble = parse_preamble(preamble_text)
        payload = read_ieee_block(scope, ":WAV:DATA?")

        expected_points = int(preamble["points"])
        if expected_points > 0 and len(payload) != expected_points:
            print(
                f"WARNING: Payload sample count {len(payload)} differs from preamble points {expected_points}",
                file=sys.stderr,
            )

        outdir.mkdir(parents=True, exist_ok=True)
        base = f"rigol_waveform_{channel}_{timestamp()}"
        csv_path = outdir / f"{base}.csv"
        json_path = outdir / f"{base}.json"

        with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["time_s", "voltage_v", "adc"])
            for index, adc in enumerate(payload):
                time_s, voltage_v = convert_sample(index, adc, preamble)
                writer.writerow([f"{time_s:.12g}", f"{voltage_v:.12g}", adc])

        metadata = {
            "idn": idn,
            "resource": resource,
            "channel": channel,
            "waveform_mode": "NORM",
            "waveform_format": "BYTE",
            "preamble_raw": preamble_text,
            "preamble": preamble,
            "sample_count": len(payload),
            "csv": str(csv_path),
            "commands": [":STOP", f":WAV:SOUR {channel}", ":WAV:MODE NORM", ":WAV:FORM BYTE", ":WAV:PRE?", ":WAV:DATA?"],
        }
        json_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        return csv_path, json_path
    finally:
        try:
            scope.close()
        finally:
            rm.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a DS1104Z waveform CSV from the displayed record.")
    parser.add_argument("--ip", required=True, help="Oscilloscope IPv4 address")
    parser.add_argument("--socket", action="store_true", help="Use TCPIP0::<IP>::5555::SOCKET instead of INSTR")
    parser.add_argument("--channel", default="CHAN1", help="Waveform source channel: CHAN1-CHAN4 or 1-4")
    parser.add_argument("--outdir", default="captures", help="Output directory")
    parser.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS, help="VISA timeout in milliseconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        csv_path, json_path = export_waveform(args)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Failed to export waveform CSV: {exc}", file=sys.stderr)
        return 1

    print(f"Saved waveform CSV: {csv_path}")
    print(f"Saved waveform JSON: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
