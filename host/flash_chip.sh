#!/bin/bash
# Usage: host/flash_chip.sh path/to/firmware.hex
# Stops blinky, flashes the ESP32 with ArduinoISP, programs the ATmega64 with avrdude (up to 4 tries), then puts the
# uart_bridge sketch back on the ESP32. Fuses are never written. Needs arduino-cli (esp32 core) and avrdude.
# Env: PORT (default /dev/ttyUSB0), AVRDUDE (default: avrdude from PATH).
set -u
HEX=$(readlink -f "$1"); HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(dirname "$HERE")
PORT=${PORT:-/dev/ttyUSB0}; AVRDUDE=${AVRDUDE:-avrdude}; FQBN=esp32:esp32:esp32
[ -f "$HERE/blinky.pid" ] && kill "$(cat "$HERE/blinky.pid")" 2>/dev/null; sleep 2
echo "$(date +%T) ESP32 -> ArduinoISP"
arduino-cli compile --upload -p "$PORT" --fqbn $FQBN "$ROOT/esp32/ArduinoISP_esp32" 2>&1 | tail -3
sleep 6
ok=0
for try in 1 2 3 4; do
  echo "$(date +%T) avrdude try $try"
  if $AVRDUDE -c arduino_as_isp -p m64 -P "$PORT" -b 19200 -U flash:w:"$HEX":i 2>&1 | tee /tmp/avrdude_last.log | tail -6 | grep -q "verified"; then ok=1; break; fi
  tail -4 /tmp/avrdude_last.log; sleep 5
done
echo "$(date +%T) flash ok=$ok"
echo "$(date +%T) ESP32 -> uart_bridge"
arduino-cli compile --upload -p "$PORT" --fqbn $FQBN "$ROOT/esp32/uart_bridge" 2>&1 | tail -2
echo "$(date +%T) done"
