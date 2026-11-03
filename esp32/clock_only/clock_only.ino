// Dedicated clock source for the treadmill console board's ATmega64 (crystal missing).
// GPIO4: 1 MHz square wave (LEDC, 1-bit, 50 % duty) -> 2 kOhm -> X1 pad (biased by 5.1 kOhm to 5 V). Nothing else.
// Power this ESP32 from a source that avrdude cannot reset (e.g. VIN from the programmer's USB 5 V).
void setup() {
  ledcAttach(4, 1000000, 1);
  ledcWrite(4, 1);
}
void loop() { delay(1000); }
