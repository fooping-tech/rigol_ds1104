---
name: rigol-ds1104z-lan
description: Use this skill when controlling a RIGOL DS1104Z oscilloscope over LAN/LXI from Python or MCP. This skill covers SCPI control, connection checks, screenshots, single-shot captures, waveform CSV export, embedded signal analysis, and measurement logging.
---

# RIGOL DS1104Z LAN Control

## Purpose

Use this skill to control a RIGOL DS1104Z oscilloscope over LAN with Python and SCPI, capture reproducible measurement evidence, and turn captured waveforms into a concise engineering report. Prefer saved evidence over visual-only conclusions: screenshot PNG, waveform CSV, setup JSON, and report Markdown belong together.

## Assumptions

- Instrument: RIGOL DS1104Z or compatible DS1000Z-family scope.
- Connection: Ethernet LAN/LXI.
- Control: Python with PyVISA and the pure-Python backend.
- First transport to try: `TCPIP0::<IP>::INSTR`.
- Fallback transport: `TCPIP0::<IP>::5555::SOCKET`.
- Waveform export starts with `:WAV:MODE NORM` for the displayed record. Deep memory export is out of scope for the baseline tools.

## Python Environment

Use `uv` for the local Python environment:

```bash
uv sync
```

Run tools through the managed environment:

```bash
uv run python tools/rigol/rigol_check_lan.py --ip <YOUR_IP_ADDR>
```

For local-only settings, copy the example config and edit it:

```bash
cp config/rigol.example.env config/rigol.env
$EDITOR config/rigol.env
```

If `--ip` is omitted, the tools read `RIGOL_IP` from `config/rigol.env` and then from the shell environment:

```bash
uv run python tools/rigol/rigol_check_lan.py
```

Use `--config <path>` for another local env file. Do not commit personal IP addresses, serial numbers, or lab-specific identifiers.

The bundled tools only require Python standard library plus `pyvisa`; `numpy`, `matplotlib`, and `pandas` are included for later analysis and plotting.

## LAN Connection Checklist

1. On the DS1104Z, open the LAN settings and note the IP address.
2. Confirm the PC and scope are on the same subnet or routed network.
3. From the PC, run `ping <IP>`.
4. Try `TCPIP0::<IP>::INSTR` first.
5. If that fails, try `TCPIP0::<IP>::5555::SOCKET`.
6. Always confirm identity with `*IDN?` before changing setup.

Minimum connection test:

```bash
uv run python tools/rigol/rigol_check_lan.py --ip <YOUR_IP_ADDR>
uv run python tools/rigol/rigol_check_lan.py --ip <YOUR_IP_ADDR> --socket
```

## Embedded Measurement Defaults

- Do not depend on AUTO setup.
- Start logic, GPIO, switch, sensor, and power-rail measurements with DC coupling.
- Confirm probe ratio on the scope and in the setup command, usually `10x`.
- Start with conservative vertical and time scales, then adjust deliberately.
- Save setup metadata with every screenshot and waveform CSV.
- Do not assert voltage or timing from a screenshot alone.
- Do not convert waveform samples until `:WAV:PRE?` has been read and parsed.

Default baseline for a 3.3 V digital signal:

- Channel: `CHAN1`
- Coupling: `DC`
- Probe: `10`
- Vertical scale: `1 V/div`
- Time scale: `5 ms/div`
- Trigger: edge, `CHAN1`, level `1.5 V`

## Probe Guidance

Before configuring the scope, tell the user exactly where to probe and what ground reference to use. Ask only for missing physical details that cannot be inferred.

Typical guidance:

- MCU GPIO: probe at the MCU pin or nearest accessible pad; ground clip to the same board ground as the MCU.
- Switch or sensor input: capture both the raw external node and the MCU-side conditioned node when possible.
- Power rail: probe at the load or MCU VDD pin, not only at the regulator output; use a short ground spring if available.
- PWM: probe the driven node and, when relevant, the load-side node.
- I2C/SPI/UART: probe the signal at the receiver pin when debugging logic thresholds or ringing.

State probe attenuation, coupling, channel assignment, and trigger source in the report.

## DS1104Z-Specific Cautions

- SCPI command availability can vary with firmware and options; verify with `*IDN?` and test commands on the actual instrument.
- `:WAV:MODE NORM` returns the displayed waveform record, not necessarily full acquisition memory.
- Binary transfers may require longer timeout than simple queries.
- The scope may retain previous front-panel settings; set every important channel, timebase, trigger, and waveform parameter explicitly.
- Some commands accept abbreviated forms, but scripts should use clear SCPI strings for readability.

## SCPI Command Style

Use explicit write/query calls. Avoid hidden setup state.

Channel setup example:

```text
:STOP
:CHAN1:DISP ON
:CHAN1:COUP DC
:CHAN1:PROB 10
:CHAN1:SCAL 1
:CHAN1:OFFS 0
```

Trigger setup example:

```text
:TRIG:MODE EDGE
:TRIG:EDGE:SOUR CHAN1
:TRIG:EDGE:SLOP NEG
:TRIG:EDGE:LEV 1.5
:TRIG:SWE SING
```

## Screenshot Capture

Use `:DISP:DATA? PNG` and save the returned IEEE binary block as PNG. Screenshots are useful for context, but they are not enough for final timing or voltage claims. Pair them with waveform CSV and JSON metadata.

## Waveform Acquisition

Use this sequence for displayed waveform export:

```text
:STOP
:WAV:SOUR CHAN1
:WAV:MODE NORM
:WAV:FORM BYTE
:WAV:PRE?
:WAV:DATA?
```

Scaling rule:

- Read `:WAV:PRE?`.
- Parse `xincrement`, `xorigin`, `xreference`, `yincrement`, `yorigin`, and `yreference`.
- Convert each ADC sample only after preamble parsing.
- Keep raw ADC values in the CSV so conversion can be audited.

## Single-Shot Capture Procedure

Use `tools/rigol/rigol_single_capture.py` when a transient must be captured once.

1. Identify the physical node and ground reference.
2. Configure channel coupling, probe ratio, vertical scale, offset, time scale, trigger source, slope, and level.
3. Arm with `:SING`.
4. Cause the event under test.
5. Stop after the requested wait period.
6. Save screenshot PNG and setup JSON.
7. Export waveform CSV with `tools/rigol/rigol_waveform_csv.py`.
8. Produce a Markdown report using `references/signal_capture_report.md`.

## Firmware and Hardware Review

Base recommendations on measured evidence:

- If voltage thresholds are clean and timing margins are wide, document the evidence and the remaining assumptions.
- If edges are slow, noisy, or have repeated threshold crossings, describe the observed crossing count, pulse widths, and timing.
- Firmware options can include filtering, debounce windows, state machines, edge qualification, and ignoring events during known invalid windows.
- Hardware options can include pull-up/down changes, RC filtering, Schmitt input buffering, shielding, shorter wiring, improved grounding, and power integrity fixes.

## Measurement Report Format

Use `references/signal_capture_report.md` for the report structure. Every report should answer:

- What waveform was captured?
- Where was the probe connected?
- What setup was used?
- What facts are visible in the CSV and screenshot?
- What is inferred, and what remains uncertain?
- What should be measured next?

## Troubleshooting

Read `references/troubleshooting.md` when LAN, PyVISA, binary transfer, screenshot, or waveform scaling fails.

## Preferred Answer Style

- Be specific about probe placement and grounding.
- Separate measured facts from interpretation.
- Cite saved PNG, CSV, and JSON filenames.
- State when no real instrument test was run.
- Do not use AUTO setup as the primary method.
- Do not make voltage/timing claims until waveform CSV is scaled from `:WAV:PRE?`.

## References

- `references/scpi_cheatsheet.md` for common DS1104Z SCPI commands.
- `references/signal_capture_report.md` for report structure and probe guidance.
- `references/waveform_csv.md` for CSV formats and scaling formulas.
- `references/troubleshooting.md` for LAN and PyVISA failure modes.
