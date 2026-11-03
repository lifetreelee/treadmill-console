import cv2,numpy as np,json,sys
exec(open('analysis/digits_decode2.py').read().split("H,W=")[0].split("code=np.load")[0])
D='photos/digits/'
def strip(i): return cv2.rotate(cv2.imread(D+f'raw{i}.jpg')[1000:3480,1740:2080], cv2.ROTATE_90_CLOCKWISE)
allon=np.maximum(strip(2)[:,:,2],strip(9)[:,:,2]).astype(np.float32)
planes=[strip(3+b)[:,:,2].astype(np.float32) for b in range(6)]
digits=[(1,82,223),(1,183,220),(1,280,218),(2,493,211),(2,597,202),(2,692,201),(3,900,196),(3,995,191),(3,1087,182),(3,1180,179),
 (4,1388,175),(4,1480,171),(4,1569,164),(4,1659,161),(5,1862,153),(5,1951,150),(5,2040,148),(6,2231,145),(6,2320,145),(6,2407,146)]
SEG={'a':(0,-42),'b':(26,-22),'c':(26,22),'d':(0,42),'e':(-26,22),'f':(-26,-22),'g':(0,0),'dpTL':(-40,-44),'dpBR':(40,44)}
def samp(img,x,y,r=4):
    return float(np.median(img[int(y)-r:int(y)+r+1,int(x)-r:int(x)+r+1]))
out={}
for g,cx,cy in digits:
    row={}
    for name,(dx,dy) in SEG.items():
        x,y=cx+dx,cy+dy
        a=samp(allon,x,y)
        bits=[samp(p,x,y)>150 for p in planes]
        row[name]=(round(a),bits)
    out[(g,cx)]=row
    print('G%d x%d '%(g,cx)+'  '.join('%s:%s'%(n,('--' if v[0]<120 else ''.join('1' if b else '0' for b in v[1][::-1]))) for n,v in row.items()))
