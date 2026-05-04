#!/usr/bin/env python3
"""Configure and run a DS1104Z single-shot edge capture."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path
from typing import Any

import pyvisa

from rigol_common import add_ip_argument, resolve_ip


DEFAULT_TIMEOUT_MS = 15000


def timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def normalize_channel(channel: str) -> str:
    value = channel.upper()
    if value in {"1", "2", "3", "4"}:
        value = f"CHAN{value}"
    if value not in {"CHAN1", "CHAN2", "CHAN3", "CHAN4"}:
        raise ValueError("channel must be CHAN1, CHAN2, CHAN3, CHAN4, or 1-4")
    return value


def slope_to_scpi(slope: str) -> str:
    if slope == "falling":
        return "NEG"
    if slope == "rising":
        return "POS"
    raise ValueError("slope must be falling or rising")


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


def write(scope: Any, command: str) -> None:
    print(command)
    scope.write(command)


def read_ieee_block(scope: Any, command: str) -> bytes:
    scope.write(command)
    raw = bytes(scope.read_raw())
    if not raw.startswith(b"#"):
        raise RuntimeError(f"{command} did not return an IEEE binary block; first bytes={raw[:16]!r}")
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


def configure_single_capture(
    scope: Any,
    channel: str,
    slope: str,
    level: float,
    probe: float,
    coupling: str,
    vertical_scale: float,
    vertical_offset: float,
    time_scale: float,
    time_offset: float,
) -> list[str]:
    slope_scpi = slope_to_scpi(slope)
    coupling = coupling.upper()
    if coupling not in {"AC", "DC", "GND"}:
        raise ValueError("coupling must be AC, DC, or GND")

    commands = [
        ":STOP",
        f":{channel}:DISP ON",
        f":{channel}:COUP {coupling}",
        f":{channel}:PROB {probe:g}",
        f":{channel}:SCAL {vertical_scale:g}",
        f":{channel}:OFFS {vertical_offset:g}",
        f":TIM:SCAL {time_scale:g}",
        f":TIM:OFFS {time_offset:g}",
        ":TRIG:MODE EDGE",
        f":TRIG:EDGE:SOUR {channel}",
        f":TRIG:EDGE:SLOP {slope_scpi}",
        f":TRIG:EDGE:LEV {level:g}",
        ":TRIG:SWE SING",
        ":SING",
    ]
    for command in commands:
        write(scope, command)
    return commands


def run_capture(args: argparse.Namespace) -> tuple[Path, Path]:
    ip = resolve_ip(args)
    channel = normalize_channel(args.channel)
    outdir = Path(args.outdir)
    rm, scope, resource = open_scope(ip, args.socket, args.timeout_ms)
    try:
        idn = str(scope.query("*IDN?")).strip()
        print(f"*IDN?: {idn}")
        commands = configure_single_capture(
            scope=scope,
            channel=channel,
            slope=args.slope,
            level=args.level,
            probe=args.probe,
            coupling=args.coupling,
            vertical_scale=args.vertical_scale,
            vertical_offset=args.vertical_offset,
            time_scale=args.time_scale,
            time_offset=args.time_offset,
        )

        print(f"Waiting {args.wait} seconds for the event...")
        time.sleep(args.wait)
        write(scope, ":STOP")

        png = read_ieee_block(scope, ":DISP:DATA? PNG")
        if not png.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("Screenshot payload was received but does not look like a PNG file")

        outdir.mkdir(parents=True, exist_ok=True)
        base = f"rigol_single_capture_{channel}_{args.slope}_{timestamp()}"
        png_path = outdir / f"{base}.png"
        json_path = outdir / f"{base}.json"
        png_path.write_bytes(png)
        metadata = {
            "measurement_purpose": args.purpose,
            "idn": idn,
            "resource": resource,
            "channel": channel,
            "coupling": args.coupling.upper(),
            "probe": args.probe,
            "vertical_scale_v_per_div": args.vertical_scale,
            "vertical_offset_v": args.vertical_offset,
            "time_scale_s_per_div": args.time_scale,
            "time_offset_s": args.time_offset,
            "trigger_mode": "EDGE",
            "trigger_source": channel,
            "trigger_slope": args.slope,
            "trigger_slope_scpi": slope_to_scpi(args.slope),
            "trigger_level_v": args.level,
            "wait_s": args.wait,
            "commands": commands + [":STOP", ":DISP:DATA? PNG"],
            "screenshot_png": str(png_path),
        }
        json_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        return png_path, json_path
    finally:
        try:
            scope.close()
        finally:
            rm.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a DS1104Z single-shot edge capture.")
    add_ip_argument(parser)
    parser.add_argument("--socket", action="store_true", help="Use TCPIP0::<IP>::5555::SOCKET instead of INSTR")
    parser.add_argument("--channel", default="CHAN1", help="Trigger/source channel: CHAN1-CHAN4 or 1-4")
    parser.add_argument("--slope", choices=["falling", "rising"], required=True, help="Trigger edge direction")
    parser.add_argument("--level", type=float, default=1.5, help="Trigger level in volts")
    parser.add_argument("--outdir", default="captures", help="Output directory")
    parser.add_argument("--wait", type=float, default=10.0, help="Seconds to wait after arming before stopping")
    parser.add_argument("--probe", type=float, default=10.0, help="Probe attenuation setting")
    parser.add_argument("--coupling", default="DC", help="Channel coupling: DC, AC, or GND")
    parser.add_argument("--vertical-scale", type=float, default=1.0, help="Volts per division")
    parser.add_argument("--vertical-offset", type=float, default=0.0, help="Vertical offset in volts")
    parser.add_argument("--time-scale", type=float, default=0.005, help="Seconds per division")
    parser.add_argument("--time-offset", type=float, default=0.0, help="Time offset in seconds")
    parser.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS, help="VISA timeout in milliseconds")
    parser.add_argument("--purpose", default="single-shot embedded signal measurement", help="Measurement purpose stored in JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        png_path, json_path = run_capture(args)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Failed to run single-shot capture: {exc}", file=sys.stderr)
        return 1

    print(f"Saved screenshot: {png_path}")
    print(f"Saved setup JSON: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
