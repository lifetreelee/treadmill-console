#!/usr/bin/env python3
# Owns the treadmill console: keeps a picture on the matrix (the smiley by default) and animates it, shows digits/bars/LEDs, polls the buttons,
# and scrolls messages. Reads display_state.json (re-read when it changes):
#   {"art": [8 strings of 20 chars, '#' = lit], "color": "y"|"r"|"g", "blink": [[x,y],...],   (blink cells = pixels that close briefly)
#    "digits": {"1": "123", "3": "8388", ...}, "dots": {"3": [1], ...},    (digit groups 1..6 left to right, see digits.py)
#    "raw": [[row, j], ...], "raw_blink": [[row, j], ...], "raw_slow": [[row, j], ...],    (extra single LEDs: bar graph, round LEDs, LED 50; see bars.py)
#    "message": {"id": "unique string", "text": "HELLO", "color": "y", "repeat": 2, "until_ack": false, "expires": epoch_seconds, "speed": 9}}
# A message scrolls over the matrix (5x7 font, see font.py): `repeat` passes, or until any button is pressed when until_ack is true (or `expires`). A button press
# always ends a message. Each message id is shown once; what happened is appended to message_ack.jsonl ({"id","how","t","text"}: how = "button S3", "finished", "expired").
# Every button press (edge) is appended to button_events.jsonl. Holds /dev/ttyUSB0: stop this (pid in blinky.pid) before reprogramming the chip.
import json,os,random,sys,time,signal
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import serial
from smiley import SMILE
import digits, font
HERE=os.path.dirname(os.path.abspath(__file__)); STATE=os.path.join(HERE,'display_state.json'); LOG=os.path.join(HERE,'blinky.log')
ACKLOG=os.path.join(HERE,'message_ack.jsonl'); BTNLOG=os.path.join(HERE,'button_events.jsonl')
EYES=[[6,1],[7,1],[6,2],[7,2],[12,1],[13,1],[12,2],[13,2]]
BUTTON={0:'D26',1:'S3',2:'S4',3:'S1',4:'S6',5:'S7',6:'S8',7:'S5',8:'S9',9:'S10',10:'S11'}   # row of the key matrix -> silkscreen name
def log(m):
    with open(LOG,'a') as f: f.write(time.strftime('%F %T ')+m+'\n')
def cmd(s,c): s.write((c+'\n').encode()); return s.read_until(b'\n').decode(errors='ignore').strip()
def zframe(red,green): return 'Z'+''.join('%02x'%m for m in red)+''.join('%02x'%m for m in green)
def art_masks(art,color):
    cols=[sum(1<<y for y in range(8) if art[y][x]=='#') for x in range(20)]
    return (cols if color in ('r','y') else [0]*20),(cols if color in ('g','y') else [0]*20)
def paint(s,art,color): cmd(s,zframe(*art_masks(art,color)))
def px(s,x,y,color,on):
    """single matrix pixel (red j = 23 - x, green j = 47 - x, row = 7 - y)"""
    r=7-y; op='p' if on else 'q'
    if color in ('r','y'): cmd(s,'%s %d %d'%(op,r,23-x))
    if color in ('g','y'): cmd(s,'%s %d %d'%(op,r,47-x))
cur_dig=set(); RB=[]; PHASE=True; RS=[]; PHASE2=True; MSG=None
def draw_digits(s,dg,dots,raw=()):
    """Update only the digit/bar/LED segments that changed."""
    global cur_dig
    new=set()
    for g,text in dg.items(): new|=digits.lit(int(g),str(text),dots.get(g,[]))
    new|={(int(r),int(j)) for r,j in raw}
    if PHASE: new|={(int(r),int(j)) for r,j in RB}
    if PHASE2: new|={(int(r),int(j)) for r,j in RS}
    for r,j in new-cur_dig: cmd(s,'p %d %d'%(r,j))
    for r,j in cur_dig-new: cmd(s,'q %d %d'%(r,j))
    cur_dig=new
def load():
    global RB,RS,MSG
    try:
        d=json.load(open(STATE)); RB=d.get('raw_blink',[]); RS=d.get('raw_slow',[]); MSG=d.get('message')
        return d.get('art',SMILE),d.get('color','y'),d.get('blink',EYES),d.get('digits',{}),d.get('dots',{}),d.get('raw',[])
    except Exception: return SMILE,'y',EYES,{},{},[]
def append(path,obj):
    with open(path,'a') as f: f.write(json.dumps(obj)+'\n')
def read_done():
    ids=set()
    try:
        for l in open(ACKLOG):
            try: ids.add(json.loads(l)['id'])
            except Exception: pass
    except OSError: pass
    return ids
running=True
def stop(*_):
    global running; running=False
signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
open(os.path.join(HERE,'blinky.pid'),'w').write(str(os.getpid()))
s=serial.Serial('/dev/ttyUSB0',115200,timeout=0.3); time.sleep(3.0); s.reset_input_buffer()
cmd(s,'L 120'); cmd(s,'X')
mt=-1; art,color,blink,dg,dots,raw=load(); paint(s,art,color); draw_digits(s,dg,dots,raw); log('started')
done=read_done(); active=None; cols=[]; pos=0; loops=0; mnext=0; speed=9.0
prev_poll=0; held=0
nxt=time.time()+random.uniform(3,7); nph=time.time()+0.35; nph2=time.time()+0.9
def start_message(m):
    global active,cols,pos,loops,mnext,speed
    active=m; cols=[0]*20+font.text_columns(str(m.get('text','')))+[0]*20; pos=0; loops=0; mnext=0
    speed=float(m.get('speed',9)); log('message %s: %s'%(m.get('id'),m.get('text')))
def finish_message(how):
    global active
    append(ACKLOG,{'id':active.get('id'),'how':how,'t':time.time(),'text':active.get('text')}); done.add(active.get('id'))
    log('message %s ended: %s'%(active.get('id'),how)); active=None; paint(s,art,color)
while running:
    try:
        m=os.path.getmtime(STATE) if os.path.exists(STATE) else 0
        if m!=mt:
            mt=m; old=(art,color); art,color,blink,dg,dots,raw=load()
            if (art,color)!=old and not active: paint(s,art,color); log('redraw')
            draw_digits(s,dg,dots,raw); nxt=time.time()+random.uniform(3,7)
        now=time.time()
        # buttons: a press = the same bit set in two consecutive polls; edges are logged, any press ends a message
        try: mask=int(cmd(s,'B')[-4:],16)
        except ValueError: mask=0
        stable=mask&prev_poll; prev_poll=mask
        newly=stable&~held; held=stable
        for r in range(11):
            if newly>>r&1:
                append(BTNLOG,{'t':now,'button':BUTTON[r],'row':r}); log('button %s'%BUTTON[r])
                if active: finish_message('button %s'%BUTTON[r])
        # messages
        if MSG and MSG.get('id') not in done and (not active or active.get('id')!=MSG.get('id')):
            if MSG.get('expires') and now>MSG['expires']: done.add(MSG.get('id')); append(ACKLOG,{'id':MSG.get('id'),'how':'expired before shown','t':now,'text':MSG.get('text')})
            else: start_message(MSG)
        if active:
            if active.get('expires') and now>active['expires']: finish_message('expired')
            elif now>=mnext:
                if pos+20>len(cols):
                    loops+=1; pos=0; mnext=now+1.5
                    cmd(s,zframe([0]*20,[0]*20))
                    if not active.get('until_ack') and loops>=int(active.get('repeat',2)): finish_message('finished')
                else:
                    w=cols[pos:pos+20]; c=active.get('color','y')
                    cmd(s,zframe(w if c in ('r','y') else [0]*20, w if c in ('g','y') else [0]*20)); pos+=1; mnext=now+1.0/speed
        elif time.time()>=nxt and blink:
            wink = random.random()<0.2 and len(blink)>=8
            cells = blink[:4] if wink else blink      # a wink closes only the first (left) eye
            for x,y in cells: px(s,x,y,color,False)
            time.sleep(0.15)
            for x,y in cells:
                if art[y][x]=='#': px(s,x,y,color,True)
            nxt=time.time()+random.uniform(3,8)
        if RB and time.time()>=nph:
            PHASE=not PHASE; draw_digits(s,dg,dots,raw); nph=time.time()+0.35
        elif not RB and not PHASE:
            PHASE=True
        if RS and time.time()>=nph2:
            PHASE2=not PHASE2; draw_digits(s,dg,dots,raw); nph2=time.time()+0.9
        elif not RS and not PHASE2:
            PHASE2=True
        time.sleep(0.03 if active else 0.08)
    except serial.SerialException as e:
        log('serial error %s'%e); time.sleep(5)
        try: s=serial.Serial('/dev/ttyUSB0',115200,timeout=0.3); time.sleep(3.0)
        except Exception: pass
log('stopped')
