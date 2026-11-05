#!/usr/bin/env python3
"""Show a 20x8 picture on the matrix for a while, then put the smiley back.
  python3 show_art.py [--seconds 60] [--color y|r|g] [--digits "1=CLA,2=UdE,3=good"] ROW0 ROW1 ... ROW7     (each row 20 chars, '#' = lit, anything else = off)
Writes the 'art'/'color'/'blink' keys of display_state.json (pole_feed leaves them alone); a detached child restores the smiley."""
import json,os,sys,time,subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); STATE=os.path.join(HERE,'display_state.json')
sys.path.insert(0,HERE); from smiley import SMILE
EYES=[[6,1],[7,1],[6,2],[7,2],[12,1],[13,1],[12,2],[13,2]]
def put(art,color,blink,overlay=None):
    d=json.load(open(STATE)); d['art']=art; d['color']=color; d['blink']=blink
    if overlay: d['overlay']=overlay
    else: d.pop('overlay',None)
    tmp=STATE+'.tmp'; json.dump(d,open(tmp,'w')); os.replace(tmp,STATE)
if __name__=='__main__':
    a=sys.argv[1:]; secs=60; color='y'; dig={}
    while a and a[0].startswith('--'):
        k=a.pop(0)
        if k=='--seconds': secs=int(a.pop(0))
        elif k=='--color': color=a.pop(0)
        elif k=='--digits': dig={g.split('=',1)[0]:g.split('=',1)[1] for g in a.pop(0).split(',') if '=' in g}
        elif k=='--restore': put(SMILE,'y',EYES); sys.exit(0)
    rows=[(r.ljust(20,'.')[:20]) for r in a[:8]]; rows+=['.'*20]*(8-len(rows))
    put(rows,color,[],{'digits':dig,'until':time.time()+secs} if dig else None)   # overlay: these digit groups say something while the picture is up
    subprocess.Popen(['bash','-c','sleep %d; python3 %s --restore'%(secs,os.path.abspath(__file__))],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print('showing for %ds'%secs)
