#!/bin/bash
# Crystal version of flash_chip.sh: the board runs from its own 13.824 MHz crystal and the ESP32 must NOT drive the clock pin.
# Usage: host/flash_chip_xtal.sh [path/to/firmware.hex]   (default firmware/display_cmd12/display_cmd12.hex)
# Steps: ESP32 -> ArduinoISP (no clock); read the signature (must be 1E 96 02: proves the chip runs on its crystal and the programmer talks to it);
#        flash the ATmega64 (fuses are NEVER written); ESP32 -> uart_bridge_xtal (115200 baud to the chip).
# Stop whatever owns the serial port first (python3 host/blinky.py). Env: PORT (default /dev/ttyUSB0), AVRDUDE (default: avrdude from PATH).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(dirname "$HERE")
HEX=$(readlink -f "${1:-$ROOT/firmware/display_cmd12/display_cmd12.hex}")
PORT=${PORT:-/dev/ttyUSB0}; AVRDUDE=${AVRDUDE:-avrdude}; FQBN=esp32:esp32:esp32
if [ -f "$HERE/blinky.pid" ] && kill -0 "$(cat "$HERE/blinky.pid")" 2>/dev/null; then echo "stop host/blinky.py first (pid $(cat "$HERE/blinky.pid"))"; exit 1; fi
echo "$(date +%T) ESP32 -> ArduinoISP (no clock)"
arduino-cli compile --upload -p "$PORT" --fqbn $FQBN "$ROOT/esp32/ArduinoISP_esp32_xtal" 2>&1 | tail -3
sleep 6
sig=0
for try in 1 2 3; do
  echo "$(date +%T) signature try $try"
  $AVRDUDE -c arduino_as_isp -p m64 -P "$PORT" -b 19200 -v 2>&1 | tee /tmp/avrdude_sig.log | tail -3
  grep -q -i "1E 96 02" /tmp/avrdude_sig.log && { sig=1; break; }; sleep 4
done
[ $sig = 1 ] || { echo "$(date +%T) SIGNATURE NOT READ: stop here (crystal not running, or wiring); nothing was written"; exit 2; }
ok=0
for try in 1 2 3 4; do
  echo "$(date +%T) flash try $try"
  if $AVRDUDE -c arduino_as_isp -p m64 -P "$PORT" -b 19200 -U flash:w:"$HEX":i 2>&1 | tee /tmp/avrdude_last.log | tail -6 | grep -q "verified"; then ok=1; break; fi
  tail -4 /tmp/avrdude_last.log; sleep 5
done
echo "$(date +%T) flash ok=$ok"
echo "$(date +%T) ESP32 -> uart_bridge_xtal"
arduino-cli compile --upload -p "$PORT" --fqbn $FQBN "$ROOT/esp32/uart_bridge_xtal" 2>&1 | tail -2
echo "$(date +%T) done"
