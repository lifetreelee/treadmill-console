"""Locate each one-segment-bit blob inside each digit using photos/digits2/raw{1..8}.jpg (bit 0..7), raw10 = all lit."""
import cv2,numpy as np,json
D='photos/digits2/'
def strip(i): return cv2.rotate(cv2.imread(D+f'raw{i}.jpg')[900:3500,1800:2160],cv2.ROTATE_90_CLOCKWISE)
def litmask(img,th=150):
    R=img[:,:,2].astype(int);G=img[:,:,1].astype(int);B=img[:,:,0].astype(int)
    return ((R>th)&(R>G+60)&(R>B+20)).astype(np.uint8)   # red/pink, not the green/yellow bar graph
all10=litmask(strip(10),170)
# digit boxes from the all-lit image: close small gaps then components
k=cv2.getStructuringElement(cv2.MORPH_RECT,(9,9))
cl=cv2.morphologyEx(all10,cv2.MORPH_CLOSE,k)
n,lab,st,cen=cv2.connectedComponentsWithStats(cl,connectivity=8)
boxes=[tuple(st[i][:4]) for i in range(1,n) if st[i][4]>2500 and st[i][3]>60 and st[i][2]<130]
boxes.sort()
print(len(boxes),'digit boxes')
for b in boxes: print(b)
json.dump([list(map(int,b)) for b in boxes],open(D+'boxes.json','w'))

centres=[(1,137),(1,231),(1,328),(2,553),(2,637),(2,735),(3,955),(3,1047),(3,1140),(3,1235),
         (4,1446),(4,1538),(4,1626),(4,1719),(5,1922),(5,2012),(5,2103),(6,2299),(6,2389),(6,2479)]
strips={i:strip(i) for i in list(range(1,9))+[10]}
masks={i:litmask(strips[i],150) for i in strips}
res={}
for g,cx in centres:
    x0,x1=cx-46,cx+46
    sub=all10[:,x0:x1]
    # bbox of the digit body: take the longest vertical run of rows lit in the central columns
    cols=all10[:,cx-20:cx+20].sum(1)
    rows=np.where(cols>8)[0]
    y0,y1=rows.min(),rows.max()
    w,h=80.0,float(y1-y0)
    row={}
    for b in range(8):
        m=masks[b+1][y0-14:y1+14,x0:x1]
        ys,xs=np.nonzero(m)
        if len(xs)<30: row[b]=None; continue
        # blob centroid, normalised: u across width (cx +-40 -> 0..1), v down the digit
        u=(xs.mean()+x0-(cx-40))/80.0; v=(ys.mean()+y0-14-y0)/h
        # spread tells whether it's one blob (bar) or several
        row[b]=(round(float(u),2),round(float(v),2),len(xs),round(float(xs.std()),0),round(float(ys.std()),0))
    res[(g,cx)]=(y0,y1,row)
    print('G%d cx%d y %d-%d'%(g,cx,y0,y1))
    for b in range(8): print('   bit%d'%b, row[b])
json.dump({str(k):[v[0],v[1],{str(b):v[2][b] for b in v[2]}] for k,v in res.items()},open(D+'onehot_blobs.json','w'))
