# Signal Capture Report Guide

Use this reference after capturing a screenshot, waveform CSV, and setup JSON. The goal is to turn oscilloscope evidence into a short engineering report that says what was measured, what can be read from the waveform, and what should happen next.

## Before Capture: Probe Instructions

Tell the user exactly where to connect the probe before arming the capture.

Minimum instruction set:

- Signal node: name the physical pin, pad, connector, test point, or component terminal.
- Ground: name the board ground point and keep the ground lead short.
- Channel: assign `CHAN1` to `CHAN4`.
- Probe attenuation: usually `10x`; confirm the scope setting matches the probe switch.
- Coupling: start with `DC` for logic, GPIO, switch, sensor, and power rails.
- Trigger: source channel, slope, level, and expected event.

Examples:

- MCU GPIO: "Connect CH1 probe tip to the MCU GPIO pad or nearest accessible trace. Connect the ground spring or ground clip to the MCU board ground next to the device."
- Power rail: "Connect CH1 tip at the load-side VDD pin, not only the regulator output. Use a short ground spring if possible."
- I2C/SPI/UART: "Connect the probe at the receiver-side pin when checking signal integrity or thresholds."
- PWM/load: "Capture the controller output first, then capture the load-side node if ringing or voltage drop is suspected."

## Report Template

```markdown
# Signal Capture Report

## Summary
- Measurement purpose:
- Captured signal:
- Result:
- Recommendation:

## Probe and Setup
- Instrument:
- `*IDN?`:
- Resource:
- Channel:
- Probe location:
- Ground reference:
- Probe attenuation:
- Coupling:
- Vertical scale:
- Time scale:
- Trigger mode:
- Trigger source:
- Trigger slope:
- Trigger level:

## Saved Evidence
- Screenshot PNG:
- Waveform CSV:
- Setup JSON:
- Report generated:

## What the Waveform Shows
- Idle or baseline voltage:
- High level:
- Low level:
- Peak voltage:
- Minimum voltage:
- Period or pulse width:
- Rise/fall behavior:
- Repeated threshold crossings:
- Noise, ringing, overshoot, or undershoot:

## Interpretation
- Measured facts:
- Likely cause:
- Uncertainty:
- Firmware implication:
- Hardware implication:

## Next Capture
- Probe:
- Trigger:
- Scale changes:
- Why this next capture matters:
```

## Reading the Evidence

- Treat the CSV as the source of truth for timing and voltage.
- Treat the screenshot as context for trigger position, channel visibility, and operator review.
- Treat setup JSON as the audit trail for coupling, scale, trigger, resource, and timestamp.
- Separate measured facts from interpretation.
- If a claim depends on threshold crossings, specify the threshold used.

## Common Report Conclusions

- Clean digital transition: one threshold crossing per edge, stable high and low levels, no meaningful overshoot or repeated crossings.
- Slow edge: transition spends too much time near the receiving threshold; recommend firmware qualification or hardware edge conditioning.
- Ringing or overshoot: repeated crossings or voltage excursions are visible; recommend checking wiring, termination, grounding, and input conditioning.
- Power dip: rail minimum and duration are visible; compare against MCU or peripheral brownout/reset limits.
- Protocol issue: waveform timing or voltage levels differ from expected bus requirements; capture both transmitter and receiver side when possible.
