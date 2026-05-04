# DS1104Z SCPI Cheatsheet

SCPI command support can vary by firmware and installed options. Always start by checking `*IDN?` on the actual instrument, then verify any command that matters to the measurement.

## Identity

```text
*IDN?
```

Returns manufacturer, model, serial number, and firmware version.

## Run Control

```text
:RUN
:STOP
:SING
:TFOR
```

- `:RUN`: continuous acquisition.
- `:STOP`: stop acquisition and freeze the current display.
- `:SING`: arm for a single trigger event.
- `:TFOR`: force a trigger when armed.

## Channel Setup

```text
:CHAN1:DISP ON
:CHAN1:COUP DC
:CHAN1:PROB 10
:CHAN1:SCAL 1
:CHAN1:OFFS 0
```

- Use `CHAN1` through `CHAN4` as needed.
- Start GPIO, logic, sensor, and power-rail work with DC coupling.
- Match `:CHAN<n>:PROB` to the physical probe attenuation.
- Set scale and offset explicitly; do not rely on previous panel state.

## Timebase

```text
:TIM:SCAL 0.005
:TIM:OFFS 0
```

- `:TIM:SCAL` is seconds per division.
- `0.005` means `5 ms/div`.
- Set offset explicitly when capture position matters.

## Trigger

```text
:TRIG:MODE EDGE
:TRIG:EDGE:SOUR CHAN1
:TRIG:EDGE:SLOP NEG
:TRIG:EDGE:SLOP POS
:TRIG:EDGE:LEV 1.5
:TRIG:SWE SING
:TRIG:STAT?
```

- `NEG`: falling edge.
- `POS`: rising edge.
- Use a level appropriate to the logic family or analog threshold under test.
- `:TRIG:STAT?` reports trigger state; exact strings can vary.

## Waveform

```text
:WAV:SOUR CHAN1
:WAV:MODE NORM
:WAV:FORM BYTE
:WAV:PRE?
:WAV:DATA?
```

- `:WAV:MODE NORM` returns the displayed record.
- `:WAV:FORM BYTE` returns 8-bit samples.
- Always parse `:WAV:PRE?` before converting ADC samples into time and voltage.

## Display

```text
:DISP:DATA? PNG
```

Returns an IEEE binary block containing a PNG screenshot. Use it as visual context, not as the only measurement evidence.

## Measurements

Examples:

```text
:MEAS:ITEM? VMAX,CHAN1
:MEAS:ITEM? VMIN,CHAN1
:MEAS:ITEM? VPP,CHAN1
:MEAS:ITEM? FREQuency,CHAN1
:MEAS:ITEM? PERiod,CHAN1
:MEAS:ITEM? PWIDth,CHAN1
:MEAS:ITEM? NWIDth,CHAN1
:MEAS:ITEM? RTIMe,CHAN1
:MEAS:ITEM? FTIMe,CHAN1
```

Use measurement queries as quick checks. For final reports, prefer CSV-derived values when the waveform has been exported and scaled.
