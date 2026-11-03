#!/usr/bin/env python3
"""Put a scrolling message on the treadmill console matrix.
  say.py "LIGHTNING 9 MI" --ack            stays (repeating) until the builder presses any button, expires after --minutes (default 120)
  say.py "HELLO" --repeat 2 --color g      scrolls twice then the face returns (no acknowledgement needed)
  say.py --status                          shows the last messages and button presses
Messages are shown once per id; acknowledgements land in message_ack.jsonl, presses in button_events.jsonl."""
import argparse, json, os, time
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(HERE, 'display_state.json')
ap = argparse.ArgumentParser(); ap.add_argument('text', nargs='?'); ap.add_argument('--ack', action='store_true'); ap.add_argument('--repeat', type=int, default=2)
ap.add_argument('--color', default='y'); ap.add_argument('--minutes', type=float, default=120); ap.add_argument('--speed', type=float, default=9); ap.add_argument('--status', action='store_true')
a = ap.parse_args()
if a.status or not a.text:
    for f in ('message_ack.jsonl', 'button_events.jsonl'):
        print('==', f)
        try: print(''.join(open(os.path.join(HERE, f)).readlines()[-8:]), end='')
        except OSError: print('(none yet)')
    raise SystemExit
st = json.load(open(S))
mid = time.strftime('%m%d-%H%M%S')
st['message'] = {'id': mid, 'text': a.text, 'color': a.color, 'repeat': a.repeat, 'until_ack': a.ack, 'expires': time.time() + a.minutes * 60, 'speed': a.speed}
tmp = S + '.tmp'; json.dump(st, open(tmp, 'w')); os.replace(tmp, S); print('message', mid, 'sent:', a.text, '(until acknowledged)' if a.ack else '(%d passes)' % a.repeat)
