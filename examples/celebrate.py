#!/usr/bin/env python3
"""Celebration animation (2026-11-04): a green sine wave 'oscillating' (an oscillating crystal) with twinkling sparks, digits '13.824' + 'good Job' (the crystal frequency).
Runs ~50 s, then holds the last frame for 20 minutes and restores the smiley (same mechanism as show_art.py)."""
import math,random,subprocess,sys,time,os
HERE=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","host"); sys.path.insert(0,HERE)   # needs host/blinky.py running
import show_art
SPARKS=[(1,0),(4,1),(8,0),(12,1),(15,0),(18,1),(2,2),(6,2),(10,1),(13,2),(17,2),(19,0),(0,1),(9,2)]
COL='RYGY'
def frame(t,final=False):
    g=[['.']*20 for _ in range(8)]
    for x in range(20):
        y=4+round(2*math.sin(2*math.pi*(x/7.0)-t*0.9))
        g[y][x]='G'
        if y<7 and (x%2==0): g[y+1][x]='G'      # a thicker line on every other column
    rnd=random.Random(int(t*3))
    for i,(x,y) in enumerate(SPARKS):
        if final or rnd.random()<0.65: g[y][x]=COL[(i+int(t*2))%4] if not final else 'RYY'[i%3]
    for x in (1,4,9,13,17): g[7][x]='Y' if g[7][x]=='.' else g[7][x]
    return [''.join(r) for r in g]
def ov(until): return {'digits':{'1':' 13','2':'824','3':'good','4':' Job'},'dots':{'1':[2]},'until':until}
t0=time.time(); n=0
while time.time()-t0<50:
    t=time.time()-t0
    show_art.put(frame(t),'y',[],ov(time.time()+40)); n+=1
    time.sleep(0.16)
fin=1200
show_art.put(frame(0,True),'y',[],ov(time.time()+fin))
subprocess.Popen(['bash','-c','sleep %d; python3 %s --restore'%(fin,os.path.join(HERE,'show_art.py'))],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print('frames written',n)
