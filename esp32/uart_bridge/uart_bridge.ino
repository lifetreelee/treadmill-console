// Clock source + serial bridge for the treadmill console board.
//  - GPIO4: 1 MHz clock into the chip's crystal pad (through 2 kOhm, biased by 5.1 kOhm to 5 V)
//  - USB serial (115200) <-> UART2 (9600 baud): GPIO23 (TX) -> J11 pin 1 -> chip RXD0 (PE0), chip TXD0 (PE1) -> J11 pin 9 -> divider -> GPIO19 (RX)
//  - GPIO5 (RESET) left as an input so the board's pull-up keeps the chip running.
void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, 19, 23);
  ledcAttach(4, 1000000, 1);
  ledcWrite(4, 1);
  pinMode(5, INPUT);
}
void loop() {
  while (Serial.available()) Serial2.write(Serial.read());
  while (Serial2.available()) Serial.write(Serial2.read());
}
