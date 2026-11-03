import numpy as np, json, collections
D='photos/digits/'
code=np.load(D+'code_map.npy')
# digit centroids/bboxes found from the all-on core components (strip coords, rotated image)
digits=[ # group, x_center, y_center, w, h
 (1,82,223),(1,183,220),(1,280,218),
 (2,493,211),(2,597,202),(2,692,201),
 (3,900,196),(3,995,191),(3,1087,182),(3,1180,179),
 (4,1388,175),(4,1480,171),(4,1569,164),(4,1659,161),
 (5,1862,153),(5,1951,150),(5,2040,148),
 (6,2231,145),(6,2320,145),(6,2407,146)]
H,W=code.shape
xs=np.array([d[1] for d in digits])
res=[]
for gi,(g,cx,cy) in enumerate(digits):
    # pixels belonging to this digit: within +-52 px in x of centre, +-70 in y, nearest centre
    y0,y1=max(0,int(cy-70)),min(H,int(cy+70)); x0,x1=max(0,int(cx-52)),min(W,int(cx+52))
    sub=code[y0:y1,x0:x1]
    yy,xx=np.mgrid[y0:y1,x0:x1]
    nearest=np.abs(xx[...,None]-xs[None,None,:]).argmin(-1)==gi
    ok=(sub>=0)&nearest
    byte=collections.Counter((sub[ok]>>3).tolist()).most_common(3)
    mode=byte[0][0]
    seg={}
    for lo in range(8):
        m=ok&(sub==(mode<<3|lo))
        n=m.sum()
        if n>=15: seg[lo]=(int(n),float(xx[m].mean()-cx),float(yy[m].mean()-cy))
    res.append((g,gi,cx,cy,mode,byte,seg))
    print('G%d digit#%d byte=%d  (top3 bytes %s)'%(g,gi,mode,byte))
    for lo in sorted(seg): print('    low%d  n=%d  dx=%+.0f dy=%+.0f'%((lo,)+seg[lo]))
json.dump([(g,gi,cx,cy,int(mode),{str(k):v for k,v in seg.items()}) for g,gi,cx,cy,mode,byte,seg in res],open(D+'digit_segments.json','w'))
