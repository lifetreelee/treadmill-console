#!/usr/bin/env python3
"""Minimal data feed for the console: shows the time and CPU load on the digits, and a bar-graph gauge.

blinky.py (host/) re-reads display_state.json whenever it changes; this script only writes that file.
Digit groups 1..6 run left to right (see host/digits.py); decimals via "dots": {"3": [3]} etc.
Run from the repo root next to a running host/blinky.py, with the state file in the same folder as blinky.py.
"""
import json, os, time
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'host')
STATE = os.path.join(HERE, 'display_state.json')
import sys; sys.path.insert(0, HERE)
import bars

def write(state):
    tmp = STATE + '.tmp'
    json.dump(state, open(tmp, 'w')); os.replace(tmp, STATE)       # atomic: blinky never sees half a file

while True:
    t = time.localtime()
    load = min(os.getloadavg()[0] / (os.cpu_count() or 1), 1.0)
    steps = round(load * 36)                                      # bar graph: 36 steps bottom to top (see docs)
    write({'digits': {'1': '%02d' % t.tm_hour, '2': '%02d' % t.tm_min, '6': '%03d' % round(load * 100)},
           'raw': bars.gauge(steps, led50=load > 0.9)})
    time.sleep(10)
