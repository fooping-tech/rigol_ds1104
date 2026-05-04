# Repository Agent Instructions

## RIGOL DS1104Z Measurements

- Use the `rigol-ds1104z-lan` skill for RIGOL DS1104Z LAN/SCPI/Python measurement work.
- Use `uv sync` to create/update the Python environment, then run tools with `uv run python ...`.
- Save reproducible evidence: screenshot PNG, waveform CSV, setup JSON, and a Markdown report.
- Start every instrument session by confirming `*IDN?`.
- Prefer `TCPIP0::<IP>::INSTR`.
- If `INSTR` fails, try `TCPIP0::<IP>::5555::SOCKET`.
- Do not assert waveform voltage or timing until `:WAV:PRE?` has been parsed.
- Do not rely on AUTO setup for repeatable measurements.
- For logic, GPIO, switch, sensor, and power-rail signals, start with DC coupling.
- Before capture, give the user specific probe-tip and ground-connection instructions.
- Keep measured facts separate from interpretation in reports.
