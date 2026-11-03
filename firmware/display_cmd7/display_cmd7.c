// Display command firmware for the treadmill console board (ATmega64, 1 MHz injected clock).
// Scans 16 rows (74HC154 on PC0..PC3, enable PC4 low) with 3 x 24-bit column chains (PA1..PA3 data, PA0 clock, data 0 = lit).
// UART0 (PE0 = RXD0 from J11 pin 1, PE1 = TXD0 to J11 pin 9) at 9615 baud (U2X, UBRR 12 at 1 MHz), 8N1, ASCII lines ending in '\n':
//   X            clear all                      F            fill all (every row, every column)
//   R r          row r only (all 72 columns)    C j          column j only (all 16 rows), j = 24*chain + k, 0..71
//   P r j        single pixel: row r, column j  A r hexhexhex   not used
//   Q b          row bit-plane: rows whose number has bit b set, all columns (b 0..3)
//   S b          column bit-plane: columns whose index j has bit b set, all rows (b 0..6)
//   p r j        set pixel (keep the rest)      q r j        clear pixel (keep the rest)
//   L n          row on-time loop count (brightness), default 60
//   ?            print "OK" (ping)
//   M            input pins seen at the END of each row's on-time since the last M, per row: 16 groups 'minPINB..minPING/maxPINB..maxPING' (6 bytes = 12 hex chars each side, PINB PINC PIND PINE PINF PING); the min/max are then reset (cmd6)
//   U / u        internal pull-ups on PORTF/PORTG on / off (cmd4)
//   A            read ADC channels 0..7 (PORTF pins): prints 8 x 4 hex digits (10-bit values) (cmd5)
//   B            pressed buttons since the last B, as 4 hex digits (bit r = the button on row r, r = 0..10; the key matrix is read on PC5), then cleared (cmd7)
//   Z <40 hex> <40 hex>   paint the whole 20x8 matrix: red column masks x = 0..19 then green column masks (bit y = row y from the top; 2 hex digits per column) (cmd7)
//   T x n v      set bit n of PORTB or PORTD (x = B or D) as an output to v (0/1) (cmd4, for finding LED 13 etc.)
// Every command replies "OK\n". Numbers are decimal.
#define F_CPU 1000000UL
#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdint.h>

static uint32_t cols[16][3];   // lit masks per row and chain; bit k = k-th clock pulse (k = 0 clocked first)
static uint8_t pa[16][24];
static uint8_t kmin[16][6], kmax[16][6];   // min / max of the input pins, sampled at the end of each row's on-time, since the last M
static volatile uint16_t klatch = 0;   // buttons seen pressed (PC5 high at the end of row r's on-time), rows 0..10
static uint8_t dwell = 60;     // row on-time loop count (brightness); L n sets it

static volatile uint8_t rxbuf[64];
static volatile uint8_t rx_head = 0, rx_tail = 0;

ISR(USART0_RX_vect) {
  uint8_t c = UDR0;
  uint8_t n = (rx_head + 1) & 63;
  if (n != rx_tail) { rxbuf[rx_head] = c; rx_head = n; }
}

static void uart_init(void) {
  UCSR0A = (1 << U2X0);
  UBRR0H = 0;
  UBRR0L = 12;                                // 1e6 / (8 * 13) = 9615 baud
  UCSR0C = (1 << UCSZ01) | (1 << UCSZ00);     // 8N1
  UCSR0B = (1 << RXEN0) | (1 << TXEN0) | (1 << RXCIE0);
}
static void uart_puts(const char *s) {
  while (*s) { while (!(UCSR0A & (1 << UDRE0))) ; UDR0 = *s++; }
}

static void uart_hex(uint8_t v) {
  const char *h = "0123456789abcdef";
  while (!(UCSR0A & (1 << UDRE0))) ; UDR0 = h[v >> 4];
  while (!(UCSR0A & (1 << UDRE0))) ; UDR0 = h[v & 15];
}

static uint16_t adc_read(uint8_t ch) {
  ADMUX = (1 << REFS0) | (ch & 7);                         // AVCC reference
  ADCSRA = (1 << ADEN) | (1 << ADPS1) | (1 << ADPS0);      // 1 MHz / 8 = 125 kHz
  for (uint8_t i = 0; i < 2; i++) { ADCSRA |= (1 << ADSC); while (ADCSRA & (1 << ADSC)) ; }   // the first conversion after a channel change is discarded
  return ADC;
}

static void io_init(void) {
  PORTA = 0x0F; DDRA = 0xFF;
  PORTB = 0x00; DDRB = 0xFD;
  PORTC = 0x10; DDRC = 0x1F;
  PORTD = 0x00; DDRD = 0x0E;
  PORTE = 0x00; DDRE = 0x00;                  // PE0/PE1 are the UART pins (UART enable overrides the directions)
}

static void build(void) {
  for (uint8_t r = 0; r < 16; r++)
    for (uint8_t k = 0; k < 24; k++) {
      uint8_t d = 0x0E;
      if (cols[r][0] & (1UL << k)) d &= ~0x02;
      if (cols[r][1] & (1UL << k)) d &= ~0x04;
      if (cols[r][2] & (1UL << k)) d &= ~0x08;
      pa[r][k] = d;
    }
}

static void scan_once(void) {
  for (uint8_t r = 0; r < 16; r++) {
    PORTC |= 0x10;
    const uint8_t *p = pa[r];
    for (uint8_t k = 0; k < 24; k++) {
      uint8_t v = *p++;
      PORTA = v;
      PORTA = v | 0x01;
    }
    PORTC = (PORTC & 0xE0) | r | 0x10;
    PORTC &= ~0x10;
    for (volatile uint8_t i = 0; i < dwell; i++) ;
    {
      uint8_t v[6] = { PINB, PINC, PIND, PINE, PINF, PING };    // row still enabled: let the pull-ups settle first
      for (uint8_t i = 0; i < 6; i++) { kmin[r][i] &= v[i]; kmax[r][i] |= v[i]; }
      if (r < 11 && (v[1] & 0x20)) klatch |= (1u << r);
    }
  }
  PORTC |= 0x10;
}

static void set_pa(uint8_t r, uint8_t j, uint8_t on) {
  uint8_t k = j % 24, bit = 0x02 << (j / 24);
  if (on) pa[r][k] &= ~bit; else pa[r][k] |= bit;        // data 0 = lit
}
static void clear_all(void) { for (uint8_t r = 0; r < 16; r++) cols[r][0] = cols[r][1] = cols[r][2] = 0; }
static void setpix(uint8_t r, uint8_t j) { cols[r][j / 24] |= 1UL << (j % 24); }
static void clrpix(uint8_t r, uint8_t j) { cols[r][j / 24] &= ~(1UL << (j % 24)); }

static uint8_t hexv(char c) { if (c >= '0' && c <= '9') return c - '0'; if (c >= 'a' && c <= 'f') return c - 'a' + 10; if (c >= 'A' && c <= 'F') return c - 'A' + 10; return 0; }

static uint8_t parse_num(const char **s) {
  while (**s == ' ') (*s)++;
  uint8_t v = 0;
  while (**s >= '0' && **s <= '9') { v = v * 10 + (**s - '0'); (*s)++; }
  return v;
}

static void run_cmd(const char *s) {
  char c = *s++;
  uint8_t nb = 1;                              // rebuild the whole scan table afterwards? (not needed for single-pixel edits)
  switch (c) {
    case 'X': clear_all(); break;
    case 'F': for (uint8_t r = 0; r < 16; r++) for (uint8_t j = 0; j < 72; j++) setpix(r, j); break;
    case 'R': { uint8_t r = parse_num(&s) & 15; clear_all(); for (uint8_t j = 0; j < 72; j++) setpix(r, j); break; }
    case 'C': { uint8_t j = parse_num(&s); if (j > 71) j = 71; clear_all(); for (uint8_t r = 0; r < 16; r++) setpix(r, j); break; }
    case 'P': { uint8_t r = parse_num(&s) & 15; uint8_t j = parse_num(&s); if (j > 71) j = 71; clear_all(); setpix(r, j); break; }
    case 'Q': { uint8_t b = parse_num(&s) & 3; clear_all(); for (uint8_t r = 0; r < 16; r++) if (r & (1 << b)) for (uint8_t j = 0; j < 72; j++) setpix(r, j); break; }
    case 'S': { uint8_t b = parse_num(&s) & 7; clear_all(); for (uint8_t j = 0; j < 72; j++) if (j & (1 << b)) for (uint8_t r = 0; r < 16; r++) setpix(r, j); break; }
    case 'p': { uint8_t r = parse_num(&s) & 15; uint8_t j = parse_num(&s); if (j > 71) j = 71; setpix(r, j); set_pa(r, j, 1); nb = 0; break; }   // set one pixel, keep the rest
    case 'q': { uint8_t r = parse_num(&s) & 15; uint8_t j = parse_num(&s); if (j > 71) j = 71; clrpix(r, j); set_pa(r, j, 0); nb = 0; break; }   // clear one pixel, keep the rest
    case 'L': { dwell = parse_num(&s); nb = 0; break; }                                                                       // brightness: 5 (dim) .. 250 (bright)
    case '?': break;
    case 'M': {
      for (uint8_t r = 0; r < 16; r++) {
        for (uint8_t i = 0; i < 6; i++) uart_hex(kmin[r][i]);
        uart_puts("/");
        for (uint8_t i = 0; i < 6; i++) uart_hex(kmax[r][i]);
        uart_puts(r == 15 ? "\n" : " ");
      }
      for (uint8_t r = 0; r < 16; r++) for (uint8_t i = 0; i < 6; i++) { kmin[r][i] = 0xFF; kmax[r][i] = 0; }
      return;
    }
    case 'A': {
      for (uint8_t ch = 0; ch < 8; ch++) { uint16_t v = adc_read(ch); uart_hex(v >> 8); uart_hex(v & 255); uart_puts(ch == 7 ? "\n" : " "); }
      return;
    }
    case 'B': {
      uint16_t k = klatch; klatch = 0;
      uart_hex(k >> 8); uart_hex(k & 255); uart_puts("\n");
      return;
    }
    case 'Z': {
      uint8_t n = 0; while (s[n]) n++;
      if (n < 80) { uart_puts("ERR\n"); return; }
      uint8_t m[40];
      for (uint8_t i = 0; i < 40; i++) m[i] = (hexv(s[2 * i]) << 4) | hexv(s[2 * i + 1]);
      for (uint8_t x = 0; x < 20; x++)
        for (uint8_t y = 0; y < 8; y++) {
          uint8_t r = 7 - y, jr = 23 - x, jg = 47 - x;
          if (m[x] >> y & 1) { setpix(r, jr); set_pa(r, jr, 1); } else { clrpix(r, jr); set_pa(r, jr, 0); }
          if (m[20 + x] >> y & 1) { setpix(r, jg); set_pa(r, jg, 1); } else { clrpix(r, jg); set_pa(r, jg, 0); }
        }
      nb = 0; break;
    }
    case 'U': PORTF = 0xFF; PORTG = 0x1F; nb = 0; break;
    case 'u': PORTF = 0x00; PORTG = 0x00; nb = 0; break;
    case 'T': {
      while (*s == ' ') s++;
      char x = *s++; uint8_t n = parse_num(&s) & 7; uint8_t v = parse_num(&s) & 1;
      if (x == 'B' && n != 1) { DDRB |= (1 << n); PORTB = (PORTB & ~(1 << n)) | (v << n); }     // PB1 is SCK of the ISP header: never touch
      else if (x == 'D') { DDRD |= (1 << n); PORTD = (PORTD & ~(1 << n)) | (v << n); }
      else { uart_puts("ERR\n"); return; }
      nb = 0; break;
    }
    default: uart_puts("ERR\n"); return;
  }
  if (nb) build();
  uart_puts("OK\n");
}

int main(void) {
  io_init();
  for (uint8_t r = 0; r < 16; r++) for (uint8_t i = 0; i < 6; i++) { kmin[r][i] = 0xFF; kmax[r][i] = 0; }
  uart_init();
  sei();
  clear_all();
  for (uint8_t r = 0; r < 16; r++) for (uint8_t j = 0; j < 72; j++) setpix(r, j);   // power-up: everything on until the first command
  build();
  char line[100]; uint8_t n = 0;
  for (;;) {
    scan_once();
    while (rx_tail != rx_head) {
      char c = rxbuf[rx_tail]; rx_tail = (rx_tail + 1) & 63;
      if (c == '\n' || c == '\r') { if (n) { line[n] = 0; run_cmd(line); n = 0; } }
      else if (n < sizeof(line) - 1) line[n++] = c;
    }
  }
}
