"""Decode (row, j) of LEDs outside the matrix/digits from photos/bar/raw{1..12}.jpg:
raw1 = all on, raw2..5 = row planes Q0..Q3, raw6..11 = column planes S0..S5, raw12 = dark."""
import cv2,numpy as np,json,sys
D='photos/bar/'
V=lambda i: cv2.GaussianBlur(cv2.imread(D+f'raw{i}.jpg').max(axis=2).astype(np.float32),(0,0),2.0)
A=V(1)
Q=[V(2+b) for b in range(4)]; S=[V(6+b) for b in range(6)]
lit=A>150
rowc=np.zeros(A.shape,np.int32); colc=np.zeros(A.shape,np.int32)
for b,p in enumerate(Q): rowc|=((p>0.6*A)&lit).astype(np.int32)<<b
for b,p in enumerate(S): colc|=((p>0.6*A)&lit).astype(np.int32)<<b
np.save(D+'rowc.npy',np.where(lit,rowc,-1)); np.save(D+'colc.npy',np.where(lit,colc,-1))
def blobs(region,minpx=250):
    y0,y1,x0,x1=region
    out=[]
    code=np.where(lit,rowc*64+colc,-1)[y0:y1,x0:x1]
    for c in np.unique(code):
        if c<0: continue
        m=(code==c).astype(np.uint8)
        n,lab,st,cen=cv2.connectedComponentsWithStats(m,connectivity=8)
        for i in range(1,n):
            if st[i][4]>=minpx: out.append((int(c)>>6,int(c)&63,int(st[i][4]),round(cen[i][0]+x0),round(cen[i][1]+y0)))
    return sorted(out,key=lambda t:(t[3],t[4]))
if __name__=='__main__':
    print('ROUND LEDs (left column x~1150-1190 and the three at y~1586)')
    for b in blobs((1380,2950,1130,1210),200)+blobs((1550,1620,1400,1660),200): print('  row %2d  j %2d  px %d  at (%d,%d)'%b)
    print('BAR GRAPH + LED50')
    for b in blobs((2980,3500,1250,1850),250): print('  row %2d  j %2d  px %d  at (%d,%d)'%b)
