import serial,time,sys
# Matrix geometry (verified from photos, red and green decoded separately):
#   20 columns x = 0..19 left->right, 8 rows y = 0..7 top->bottom (hardware row r = 7 - y, row 0 at the bottom)
#   red LED   of column x: chain 0, clock bit k = 23 - x  -> column index j = 23 - x
#   green LED of column x: chain 1, clock bit k = 23 - x  -> column index j = 47 - x
#   both on = yellow
def jred(x): return 23 - x
def jgreen(x): return 47 - x
SMILE=[
 "....................",
 "......##....##......",
 "......##....##......",
 "....................",
 "...#..............#.",
 "....#............#..",
 ".....##........##...",
 ".......########.....",
]
def open_port():
    s=serial.Serial('/dev/ttyUSB0',115200,timeout=0.5); time.sleep(3.0); s.reset_input_buffer(); return s
def cmd(s,c):
    s.write((c+'\n').encode()); time.sleep(0.05); return s.read(20)
def pixel(s,x,y,color='y',on=True):
    r=7-y; op='p' if on else 'q'
    if color in ('r','y'): cmd(s,'%s %d %d'%(op,r,jred(x)))
    if color in ('g','y'): cmd(s,'%s %d %d'%(op,r,jgreen(x)))
def draw(s,art,color='y',clear=True):
    if clear: cmd(s,'X')
    for y,line in enumerate(art):
        for x,ch in enumerate(line):
            if ch=='#': pixel(s,x,y,color)
if __name__=='__main__':
    s=open_port()
    cmd(s,'L 120')
    draw(s,SMILE,'y')
    print('yellow smiley drawn')
