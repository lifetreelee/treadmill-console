# Replacing the injected clock with a real crystal (13.824 MHz) and the problems that followed

The first version of this project ran the ATmega64 from a 1 MHz square wave injected from the ESP32 (see `HARDWARE_MAP.md`),
because the original crystal on pad X1 was missing. On 2026-11-04 a real crystal went on X1: **13.824 MHz**, salvaged from an old
cordless-phone board (a low-profile HC-49-style SMD can). The board's footprint has through-holes under the part, so the old
part could be moved by heating from the back of the board. Everything below was found the hard way; it is written down so the next person does not have to.

## Why 13.824 MHz is a good crystal for this chip
13,824,000 / 921,600 = 15 exactly, so the UART runs at exactly 115200 baud with U2X and `UBRR = 14` (and 57600, 38400, 19200, 9600 are exact too).
It is within the ATmega64-16AU's 16 MHz rating. The chip's fuses (read-only reads; this project never writes them): `lfuse 0xFF`, `hfuse 0xCF`
(SPI enabled, **CKOPT programmed = full-swing oscillator**, fine for 1-16 MHz), `efuse 0xFF`. Two load capacitors (C45, C46) are already on the board next to X1;
no resistors are needed (the AVR has the oscillator inverter and its feedback on chip).

## Fitting it
- Remove the clock injection first (GPIO4 wire, series and bias resistors): two sources on XTAL1 fight. With the crystal fitted, GPIO4 must be an input (the `*_xtal` sketches do that).
- Both ends of the can must be properly soldered. The first attempt gave a dark board: only one end made contact (continuity to the load capacitors looked fine; it was not enough).
- A bad crystal is silent: the chip does not answer the programmer (`Device signature = 00 00 00`). To prove it runs, `esp32/baud_scan` tries a ladder of baud rates and reports the ones that get an "OK"; with the firmware's UBRR the reply baud is `f_clock / 120`, so a working crystal shows answers around 115,200.
- A working check: `host/flash_chip_xtal.sh` reads the signature (needs `-v` for avrdude to print it) and stops before writing if it is not `1E 96 02`.

## Firmware changes (display_cmd8 .. display_cmd12; `firmware/display_cmd12` is current)
1. **cmd8**: `F_CPU 13824000`, `UBRR0L = 14`, ADC prescaler 128 (108 kHz), and the row on-time loop multiplied by 14 so the on-time and the key settle time stay the same in real time.
2. **cmd9: the receive buffer.** At 115200 baud a whole `Z` frame (81 characters) arrives in 7 ms, longer than one scan plus a command, and a 64-byte ring buffer overflowed: 16 of 20 frames were corrupted (a smiley's mouth disappeared while single-pixel commands kept working). The ring is now 256 bytes (uint8 indices wrap by themselves).
3. **cmd10 / cmd11: ghost LEDs.** At 13.8 MHz some LEDs that nobody asked for stayed lit (brighter when more of the display was lit, present with any picture, gone after a full clear). The row driver was still conducting while the next row's data was shifted in: 24 bits take about 50 us at 1 MHz but only 3.5 us at 13.8 MHz. A wait of about 20 us after the row is switched off (before the shift) removed them. A faint ghost of the matrix columns can remain on one digit group when it has nothing to show.
4. **cmd12**: the waits are tunable at run time with `D a b c` (row-off wait in units of 4 cycles, wait after the address changes in units of 4 cycles, wait between clock edges in units of 3 cycles; defaults `D 70 7 1`). The line `L n` (row on-time, brightness) is unchanged (30 is a good value, flicker-free).

## Programming (see also `host/flash_chip_xtal.sh`)
`host/flash_chip_xtal.sh` puts `esp32/ArduinoISP_esp32_xtal` (ArduinoISP without the clock) on the ESP32, checks the signature, flashes `firmware/display_cmd12/display_cmd12.hex`, and puts `esp32/uart_bridge_xtal` (115200 to the chip) back. Fuses are never written.

## Rolling back
Remove the crystal (or leave it) and restore the injection from `HARDWARE_MAP.md`; flash `firmware/display_cmd7` with `host/flash_chip.sh`.
