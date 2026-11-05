#!/usr/bin/env python3
"""Show one of the pictures in pictures.json on the console matrix for a while, then put the smiley back.
  python3 examples/show_picture.py            lists the pictures
  python3 examples/show_picture.py dolly [--seconds 300]
Needs host/blinky.py running (it draws display_state.json). Pictures use '#' = picture colour, R/G/Y = per-pixel red/green/orange."""
import json,os,subprocess,sys,time
HERE=os.path.dirname(os.path.abspath(__file__)); HOST=os.path.join(HERE,'..','host'); sys.path.insert(0,HOST)
import show_art
doc=json.load(open(os.path.join(HERE,'pictures.json'))); pics={p['name']:p for p in doc['pictures']}
a=sys.argv[1:]
if not a or a[0] not in pics:
    for p in doc['pictures']: print('%-20s %s' % (p['name'], p.get('caption','')))
    sys.exit(0)
secs=int(a[a.index('--seconds')+1]) if '--seconds' in a else 300
p=pics[a[0]]
ov={'digits':p['digits'],'dots':p.get('dots',{}),'until':time.time()+secs} if p.get('digits') else None
show_art.put(p['art'],p['color'],[],ov)
subprocess.Popen(['bash','-c','sleep %d; python3 %s --restore'%(secs,os.path.join(HOST,'show_art.py'))],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print('showing %s for %d s'%(p['name'],secs))
