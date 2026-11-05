"""Six 7-segment digit groups on the treadmill console board (decoded 2026-11-03 from photos/digits2).
Viewing the board with the digits upright (the way a person reads them; in a portrait photo of the board this is the strip
rotated 90 deg COUNTER-clockwise, group 1 = top of the photo), groups run 1..6 left to right. Each group is one hardware
row, each digit one byte of the 72-bit column chain (j = 8*byte + bit), bit order inside a byte: dp g f e d c b a.
(First attempt read the photos rotated the wrong way, 180 deg off; the builder caught it on the live test.)"""
ROW   = {1: 8, 2: 9, 3: 12, 4: 13, 5: 10, 6: 11}
BYTES = {1: [0, 1, 2], 2: [0, 1, 2], 3: [1, 2, 4, 5], 4: [1, 2, 4, 5], 5: [0, 1, 2], 6: [0, 1, 2]}   # digit 0 = leftmost
BIT   = {'dp': 0, 'g': 1, 'f': 2, 'e': 3, 'd': 4, 'c': 5, 'b': 6, 'a': 7}
GLYPH = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc',
         '8': 'abcdefg', '9': 'abcdfg', '-': 'g', ' ': '', '_': 'd', 'E': 'afged', 'F': 'afge', 'C': 'afed', 'H': 'fgebc',
         'L': 'fed', 'P': 'abfge', 'o': 'gecd', 'r': 'ge', 'n': 'gec', 'u': 'edc', 'U': 'bcdef', 'A': 'abcefg', 'a': 'abcdeg', 'b': 'fgecd', 'd': 'bcdeg',
         'h': 'fgec', 't': 'fged', 'i': 'c', 'c': 'ged', 'e': 'abdefg', 'g': 'abfgcd', 'y': 'fgbcd', 'S': 'afgcd', 'O': 'abcdef',
         'J': 'bcde', 'l': 'ef', 'G': 'afedc', 'q': 'abfgc', 'k': 'fgebc'}
def lit(group, text, dots=()):
    """Set of (row, j) lit for a group showing `text` (one char per digit, right-aligned if shorter);
    `dots` = digit indices (0 = leftmost) whose own decimal point is lit."""
    n = len(BYTES[group]); text = text[-n:].rjust(n)
    out = set()
    for i, ch in enumerate(text):
        for seg in GLYPH.get(ch, ''):
            out.add((ROW[group], 8 * BYTES[group][i] + BIT[seg]))
    for i in dots:
        out.add((ROW[group], 8 * BYTES[group][i] + BIT['dp']))
    return out
def all_off():
    return {(ROW[g], 8 * b + k) for g in ROW for b in BYTES[g] for k in range(8)}
