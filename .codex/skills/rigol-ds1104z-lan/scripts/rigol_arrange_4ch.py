#!/usr/bin/env python3
"""Enable CH1-CH4 and arrange traces from top to bottom on a DS1104Z."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import pyvisa

from rigol_common import add_ip_argument, resolve_ip


DEFAULT_TIMEOUT_MS = 10000


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


def query_float(scope: Any, command: str) -> float:
    return float(str(scope.query(command)).strip())


def query_text(scope: Any, command: str) -> str:
    return str(scope.query(command)).strip()


def query_optional(scope: Any, command: str) -> str:
    try:
        return query_text(scope, command)
    except Exception as exc:  # noqa: BLE001
        return f"unavailable: {exc}"


def arrange_channels(args: argparse.Namespace) -> Path:
    ip = resolve_ip(args)
    outdir = Path(args.outdir)
    rm, scope, resource = open_scope(ip, args.socket, args.timeout_ms)
    try:
        idn = query_text(scope, "*IDN?")
        print(f"*IDN?: {idn}")

        before: dict[str, dict[str, float | str]] = {}
        after: dict[str, dict[str, float | str]] = {}
        target_positions_div = {
            "CHAN1": args.ch1_position_div,
            "CHAN2": args.ch2_position_div,
            "CHAN3": args.ch3_position_div,
            "CHAN4": args.ch4_position_div,
        }

        scope.write(":STOP")
        for channel in ("CHAN1", "CHAN2", "CHAN3", "CHAN4"):
            scale = query_float(scope, f":{channel}:SCAL?")
            before[channel] = {
                "display": query_text(scope, f":{channel}:DISP?"),
                "coupling": query_text(scope, f":{channel}:COUP?"),
                "probe": query_text(scope, f":{channel}:PROB?"),
                "scale_v_per_div": scale,
                "offset_v": query_float(scope, f":{channel}:OFFS?"),
            }

            target_offset_v = target_positions_div[channel] * scale
            scope.write(f":{channel}:DISP ON")
            scope.write(f":{channel}:OFFS {target_offset_v:.9g}")

            after[channel] = {
                "display": query_text(scope, f":{channel}:DISP?"),
                "coupling": query_text(scope, f":{channel}:COUP?"),
                "probe": query_text(scope, f":{channel}:PROB?"),
                "scale_v_per_div": query_float(scope, f":{channel}:SCAL?"),
                "offset_v": query_float(scope, f":{channel}:OFFS?"),
                "target_position_div": target_positions_div[channel],
            }

        setup = {
            "idn": idn,
            "resource": resource,
            "timestamp": timestamp(),
            "action": "enabled CH1-CH4 and arranged display order CH1, CH2, CH3, CH4 from top to bottom",
            "commands": [
                ":STOP",
                ":{channel}:DISP ON",
                ":{channel}:OFFS <computed from current scale and target_position_div>",
            ],
            "before": before,
            "after": after,
            "timebase": {
                "scale_s_per_div": query_float(scope, ":TIM:SCAL?"),
                "offset_s": query_float(scope, ":TIM:OFFS?"),
            },
            "trigger": {
                "mode": query_text(scope, ":TRIG:MODE?"),
                "sweep": query_text(scope, ":TRIG:SWE?"),
                "status": query_text(scope, ":TRIG:STAT?"),
                "edge_source": query_optional(scope, ":TRIG:EDGE:SOUR?"),
                "edge_slope": query_optional(scope, ":TRIG:EDGE:SLOP?"),
                "edge_level_v": query_optional(scope, ":TRIG:EDGE:LEV?"),
            },
        }

        outdir.mkdir(parents=True, exist_ok=True)
        path = outdir / f"rigol_arrange_4ch_{setup['timestamp']}.json"
        path.write_text(json.dumps(setup, indent=2) + "\n", encoding="utf-8")
        return path
    finally:
        try:
            scope.close()
        finally:
            rm.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enable CH1-CH4 and arrange DS1104Z traces top-to-bottom.")
    add_ip_argument(parser)
    parser.add_argument("--socket", action="store_true", help="Use TCPIP0::<IP>::5555::SOCKET instead of INSTR")
    parser.add_argument("--outdir", default="captures", help="Output directory")
    parser.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS, help="VISA timeout in milliseconds")
    parser.add_argument("--ch1-position-div", type=float, default=3.0, help="Target CH1 vertical position in divisions")
    parser.add_argument("--ch2-position-div", type=float, default=1.0, help="Target CH2 vertical position in divisions")
    parser.add_argument("--ch3-position-div", type=float, default=-1.0, help="Target CH3 vertical position in divisions")
    parser.add_argument("--ch4-position-div", type=float, default=-3.0, help="Target CH4 vertical position in divisions")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        path = arrange_channels(args)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Failed to arrange channels: {exc}", file=sys.stderr)
        return 1

    print(f"Saved setup JSON: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
