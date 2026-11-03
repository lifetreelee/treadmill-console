"""Decode digit segments from the column-plane photos (photos/digits/raw{1..9}.jpg).
raw2/raw9 = all on, raw3..raw8 = S0..S5 (column bit 0..5), raw1 = dark.
Strip = original crop [1000:3480, 1740:2080] rotated 90 deg clockwise (digits read upright, groups left->right)."""
import cv2, numpy as np, json
D='photos/digits/'
def strip(i):
    return cv2.rotate(cv2.imread(D+f'raw{i}.jpg')[1000:3480,1740:2080], cv2.ROTATE_90_CLOCKWISE)
allon=np.maximum(strip(2)[:,:,2],strip(9)[:,:,2]).astype(np.int32)
planes=[strip(3+b)[:,:,2].astype(np.int32) for b in range(6)]
blur=lambda a: cv2.GaussianBlur(a.astype(np.float32),(0,0),2.0)
TH=150
lit_all=blur(allon)>TH
code=np.zeros(allon.shape,np.int32)
for b,p in enumerate(planes):
    code|=((blur(p)>TH).astype(np.int32)<<b)
code[~lit_all]=-1
np.save(D+'code_map.npy',code)
# connected components of equal code
out=[]
for c in np.unique(code):
    if c<0: continue
    m=(code==c).astype(np.uint8)
    n,lab,st,cen=cv2.connectedComponentsWithStats(m,connectivity=8)
    for k in range(1,n):
        if st[k,cv2.CC_STAT_AREA]>=25:
            out.append((int(c),float(cen[k][0]),float(cen[k][1]),int(st[k,cv2.CC_STAT_AREA])))
json.dump(out,open(D+'digit_components.json','w'))
print(len(out),'components')
