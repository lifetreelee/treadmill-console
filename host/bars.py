"""Bar graph, 12 round green LEDs and square LED 50 on the treadmill console (decoded 2026-11-03 from photos/bar; verify live).
Everything is (hardware row, column j). Bar graph: 9 working bars, each with 4 bumps = rows 8..11.
Bars in photo order (yellow, yellow, yellow, green x4, pink x2) use j = 47,46,45,44,43,42,41,40,39. A 10th (dark red) bar never lights.
Round LEDs: j 35,36,37 x rows 8..11 (12 LEDs). LED 50 (square red): row 11, j 38."""
BAR_J = [47, 46, 45, 44, 43, 42, 41, 40, 39]
BAR_ROWS = [8, 9, 10, 11]
ROUND = [(11, 37), (8, 36), (9, 36), (10, 36), (11, 36), (8, 35), (9, 35), (10, 35), (11, 35), (10, 37), (9, 37), (8, 37)]  # first 9 along one edge, last 3 the short column
LED50 = (11, 38)
def bar(n, rows=BAR_ROWS):
    """first n bars fully lit"""
    return [[r, j] for j in BAR_J[:n] for r in rows]

# the builder's silkscreen labels for the round LEDs (verified live 2026-11-03): the long row of 10 runs LED 6, 9, 10, 11, 12, 1, 2, 7, 8, 13 (left to right);
# the 3 on the side are LED 5, 4, 3 (bottom up). Our first 9 entries of ROUND are the long row positions 1..9 (LED 6 ... LED 8); LED 13 (far right, the 10th)
# is NOT in the 16 x 72 row/column grid (it never lights in any plane photo, not even all-on): probably a direct pin; find it with the buttons.
ROUND_LABELS = [6, 9, 10, 11, 12, 1, 2, 7, 8, 5, 4, 3]

def gauge(steps, led50=False):
    """bar graph filled from the bottom: steps 0..36 (4 bumps per bar, bars in BAR_J order); led50 also lights the square LED"""
    full, part = divmod(steps, 4)
    raw = [[r, j] for j in BAR_J[:full] for r in BAR_ROWS]
    if full < len(BAR_J): raw += [[r, BAR_J[full]] for r in BAR_ROWS[:part]]
    if led50: raw += [[LED50[0], LED50[1]]]
    return raw
