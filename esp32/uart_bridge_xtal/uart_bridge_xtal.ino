// Serial bridge for the treadmill console board running from its own 13.824 MHz crystal (no clock injection).
//  - USB serial (115200) <-> UART2 (115200): GPIO23 (TX) -> J11 pin 1 -> chip RXD0 (PE0), chip TXD0 (PE1) -> J11 pin 9 -> divider -> GPIO19 (RX)
//  - GPIO4 is left as an input: with a crystal fitted it must NOT drive XTAL1. GPIO5 (RESET) is an input so the board's pull-up keeps the chip running.
void setup() {
  Serial.begin(115200);
  Serial2.begin(115200, SERIAL_8N1, 19, 23);
  pinMode(4, INPUT);
  pinMode(5, INPUT);
}
void loop() {
  while (Serial.available()) Serial2.write(Serial.read());
  while (Serial2.available()) Serial.write(Serial2.read());
}
