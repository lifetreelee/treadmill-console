# Hardware map: Digital Concepts treadmill console (ATmega64-16AU)

All of this was decoded from photos and a multimeter, then confirmed by live tests. Where something is a
theory it says so.

## Parts

- **U1**: ATmega64-16AU (rated 16 MHz). Crystal X1 was missing on our board; a clock is injected instead (below).
- **74HC154** row decoder: 16 rows on PC0..PC3 (address), PC4 = enable (active low).
- **3 x 74ACT164** chains (24 clocks each): data PA1/PA2/PA3, shared clock PA0. Data 0 = LED lit.
  Column index `j = 24*chain + k`, 72 columns; columns 64..71 light nothing.
- **Buttons**: a key matrix read on a single input pin, PC5, with rows 0..10 selected by the row decoder (see below).
- Serial: UART0 on the J11 header (9600-ish baud at the 1 MHz clock: UBRR 12 with U2X = 9615 baud).

## Clock injection (no crystal)

A 1 MHz square wave from an ESP32 GPIO through 2 kohm, with a 5.1 kohm bias, into the X1 crystal pad. Works
because the oscillator input is a high-gain inverter. A real crystal (11.0592 MHz is the natural choice for
exact baud rates) removes the dependency. Fuses were never written.

## Programming

The ESP32 runs `esp32/ArduinoISP_esp32/` (ArduinoISP). Lesson: the RESET release after a programming
attempt needs about 120 ms or the next attempt flakes out (`L 120` and the delay in the sketch). `avrdude -c arduino_as_isp -p m64 -b 19200`.
Afterwards the ESP32 is flashed with `esp32/uart_bridge/` (USB serial at 115200 <-> chip UART).

## Dot matrix (20 x 8, red/green, rows 0..7 top to bottom, columns 0..19 left to right)

Hardware row `r = 7 - y`. Red `j = 23 - x`, green `j = 47 - x`; both lit = orange.

## Seven-segment digit groups

Six groups left to right = hardware rows 8, 9, 12, 13, 10, 11 with 3, 3, 4, 4, 3, 3 digits. Each digit is one
byte of the chain (`j = 8*byte + bit`). Bytes, left to right: groups 1, 2, 5, 6 use [0, 1, 2]; groups 3, 4 use
[1, 2, 4, 5]. Bit order inside a byte: dp = 0, g = 1, f = 2, e = 3, d = 4, c = 5, b = 6, a = 7.
Decimal points: 3-digit groups bottom right; 4-digit groups: digits 1 and 2 bottom right, digits 3 and 4 top
(at the digit's left). Everything is in `host/digits.py`.

**Lesson:** the first decode was rotated 180 degrees because the portrait photos were read the wrong way. Always
confirm orientation with a live test before trusting a photo decode.

## Bar graph, round LEDs, square LED

- 9 working bars `j = 47, 46, 45, 44, 43, 42, 41, 40, 39` (yellow x3, green x4, red x2); each bar has 4 bumps on
  rows 8..11. Fill bottom up in that order: 36 steps (`bars.gauge`). Some LEDs on our board are missing or broken.
- 12 round LEDs: `j` 35, 36, 37 x rows 8..11 (`bars.ROUND` order; silkscreen labels in `bars.ROUND_LABELS`).
- Square red LED 50 = four LEDs in one package: `j = 38`, rows 8..11.
- Silkscreen LED 13 is not in the 16 x 72 grid (it never lit in any photo). Theory: a serial activity light.

## Buttons

11 buttons on one input pin (PC5). Rows 0..10 = D26, S3, S4, S1, S6, S7, S8, S5, S9, S10, S11. They are not an
ADC ladder (we measured). The firmware samples at the END of each row's on-time, so a press needs about half a
second; the firmware latches presses (`B` command returns 4 hex digits) and the host requires two consecutive polls.

## Firmware protocol (display_cmd7)

ASCII lines over UART, `\n` terminated: `X` clear, `F` fill, `p r j` set pixel, `q r j` clear pixel,
`Z` + 40 hex red column masks + 40 hex green masks (whole matrix, bit y = row y from top), `B` button latch,
`L n` brightness (row on-time), `?` ping, plus probe commands used during reverse engineering (`R`, `C`, `P`,
`Q`, `S`, `A`, `M`, `T`). See the header of `firmware/display_cmd7/display_cmd7.c`.

## How the mapping was found (method)

1. Photographed the board front and back, identified the chips, traced the row decoder and shift chains.
2. Wrote a firmware that lights single pixels, rows, columns and binary bit-planes on command.
3. Photographed each plane (`photos/bitplanes`, `digits`, `digits2`, `bar`) and decoded which physical LED
   lit for each (`analysis/`). Bump-level sampling beats pixel-level decoding when bloom merges neighbours.
4. Verified every guess with a live demo watched by the board's owner.
