# DS1104Z LAN and PyVISA Troubleshooting

## `ping` Fails

- Confirm the DS1104Z IP address in Utility/LAN settings.
- Confirm the PC is on the same subnet or has a route to the instrument.
- Check Ethernet link lights and cable.
- Try assigning a static IP on the same subnet.
- Firewall rules can block ICMP, but if both ping and VISA fail, fix network reachability first.

## PyVISA Cannot Find the Scope

Discovery is not required. Open the resource directly:

```python
rm = pyvisa.ResourceManager("@py")
scope = rm.open_resource("TCPIP0::192.168.1.100::INSTR")
```

If `INSTR` fails, try socket mode:

```python
scope = rm.open_resource("TCPIP0::192.168.1.100::5555::SOCKET")
scope.write_termination = "\n"
scope.read_termination = "\n"
```

## Direct LAN Check

Run:

```bash
uv run python tools/rigol/rigol_check_lan.py --ip 192.168.1.100
uv run python tools/rigol/rigol_check_lan.py --ip 192.168.1.100 --socket
```

Both commands query `*IDN?`. Do not continue measurement setup until identity is known.

## Socket Mode Timeout

- Ensure `write_termination` and `read_termination` are set to `\n`.
- Increase timeout for screenshot or waveform binary transfer.
- Close and reopen the resource after a failed binary transfer.
- Confirm no other script or MCP server is holding the socket.

## Binary Transfer Fails

- Use explicit binary block parsing for `:DISP:DATA? PNG` and `:WAV:DATA?`.
- Increase timeout to at least 10 seconds for screenshots.
- Stop acquisition before waveform export.
- If a read times out after partial data, close and reopen the resource before retrying.

## Wrong Voltage Scale

- Confirm physical probe switch is 1x or 10x.
- Confirm scope channel probe setting with `:CHAN<n>:PROB`.
- Confirm DC coupling for logic, GPIO, sensor, and power rails.
- Parse `:WAV:PRE?`; do not guess `yincrement` or `yreference`.
- Check whether the waveform source channel matches the visible channel.

## Screenshot Command Fails

- Confirm the model and firmware with `*IDN?`.
- Try again after `:STOP`.
- Increase timeout.
- Verify the returned data starts with an IEEE binary block header such as `#9...`.

## Waveform CSV Looks Wrong

- Verify `:WAV:SOUR <channel>`, `:WAV:MODE NORM`, and `:WAV:FORM BYTE`.
- Confirm the preamble has 10 fields.
- Confirm sample count matches the binary payload length.
- Check whether the channel is enabled and the signal is on screen.
- Re-run with a simple known signal before interpreting a critical measurement.
