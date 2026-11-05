// Finds the chip's real UART speed (so its real clock): the firmware sets UBRR 14 with U2X, so baud = f_clock / 120 (115200 at 13.824 MHz).
// Tries a ladder of baud rates on the chip UART (GPIO19 RX, GPIO23 TX); prints the ones that answer "OK" to '?' on USB serial. GPIO4/5 are inputs.
void setup() { Serial.begin(115200); pinMode(4, INPUT); pinMode(5, INPUT); Serial2.begin(115200, SERIAL_8N1, 19, 23); }
void loop() {
  int hits = 0;
  for (float b = 4000; b < 400000; b *= 1.02f) {
    Serial2.updateBaudRate((unsigned long)b);
    delay(5);
    while (Serial2.available()) Serial2.read();
    Serial2.print("\n?\n");
    delay(40);
    int n = 0; char buf[8];
    while (Serial2.available() && n < 7) buf[n++] = Serial2.read();
    if (n >= 2) { buf[n] = 0; hits++; Serial.printf("answer at %lu baud (%d bytes: %02x %02x)\n", (unsigned long)b, n, buf[0], buf[1]); }
  }
  Serial.printf("scan done, hits=%d\n", hits);
  delay(500);
}
