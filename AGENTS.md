# Repository Agent Instructions

## RIGOL DS1104Z Measurements

- Use the `rigol-ds1104z-lan` skill for RIGOL DS1104Z LAN/SCPI/Python measurement work.
- For Skill-bundled tools, prefer `uv run --with pyvisa --with pyvisa-py python <SKILL_DIR>/scripts/...`.
- Use `uv sync` for repository development or when intentionally using the checked-in `pyproject.toml` and `uv.lock`.
- Save reproducible evidence: screenshot PNG, waveform CSV, setup JSON, and a Markdown report.
- Start every instrument session by confirming `*IDN?`.
- Prefer `TCPIP0::<IP>::INSTR`.
- If `INSTR` fails, try `TCPIP0::<IP>::5555::SOCKET`.
- Do not assert waveform voltage or timing until `:WAV:PRE?` has been parsed.
- Do not rely on AUTO setup for repeatable measurements.
- For logic, GPIO, switch, sensor, and power-rail signals, start with DC coupling.
- Before capture, give the user specific probe-tip and ground-connection instructions.
- Keep measured facts separate from interpretation in reports.

## Open Source Repository Structure

Keep this repository structure so users can install and inspect the Skill easily:

```text
.codex/
  skills/
    rigol-ds1104z-lan/
      SKILL.md
      scripts/
      config/
      references/
pyproject.toml
uv.lock
README.md
AGENTS.md
```

If bundling a Claude Code project skill directly, the same Skill may also be placed at `.claude/skills/rigol-ds1104z-lan/`. Keep `.codex/skills/` and `.claude/skills/` synchronized if both are committed. To avoid duplicate maintenance, prefer documenting the copy/install steps in `README.md` instead of committing both copies.
