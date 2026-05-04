# Waveform CSV and Scaling

Use waveform CSV exports for quantitative timing and voltage analysis. Do not infer exact voltage or timing from a screenshot alone.

## Raw CSV Format

Use raw ADC export when preserving the original instrument samples:

```csv
index,adc
0,127
1,128
2,130
```

## Converted CSV Format

Use converted export for analysis:

```csv
time_s,voltage_v,adc
0.000000000,0.012000,127
0.000001000,0.020000,128
0.000002000,0.036000,130
```

Keep `adc` in the converted CSV so the conversion remains auditable.

## Setup JSON Format

Save metadata next to the CSV:

```json
{
  "idn": "RIGOL TECHNOLOGIES,DS1104Z,...",
  "resource": "TCPIP0::192.168.1.100::INSTR",
  "channel": "CHAN1",
  "waveform_mode": "NORM",
  "waveform_format": "BYTE",
  "preamble": {
    "format": 0,
    "type": 0,
    "points": 1200,
    "count": 1,
    "xincrement": 0.000001,
    "xorigin": 0.0,
    "xreference": 0.0,
    "yincrement": 0.008,
    "yorigin": 0.0,
    "yreference": 127.0
  },
  "sample_count": 1200
}
```

## `:WAV:PRE?` Fields

Expected DS1000Z-family preamble field order:

1. `format`
2. `type`
3. `points`
4. `count`
5. `xincrement`
6. `xorigin`
7. `xreference`
8. `yincrement`
9. `yorigin`
10. `yreference`

If the preamble has fewer than 10 comma-separated fields, stop and report an explicit error. Firmware can vary; verify on the actual instrument.

## Time and Voltage Conversion

For sample index `i` and ADC value `adc`:

```text
time_s = (i - xreference) * xincrement + xorigin
voltage_v = (adc - yorigin - yreference) * yincrement
```

Store the exact parsed preamble with every CSV. If the scale looks wrong, inspect `probe`, channel scale, coupling, and the preamble values before interpreting the signal.

## Useful Analysis Metrics

For digital and embedded signals, compute:

- Threshold crossing count.
- Falling transition count.
- Rising transition count.
- Pulse widths above or below a chosen threshold.
- Minimum pulse width.
- Longest pulse width.
- Minimum voltage.
- Maximum voltage.
- Peak-to-peak voltage.
- Period and frequency for repeated signals.
- Rise and fall time when thresholds are defined.
- Duration of noise, ringing, overshoot, or undershoot relative to a threshold.

Always state the threshold and whether values were measured from CSV, scope measurement queries, or visual inspection.
