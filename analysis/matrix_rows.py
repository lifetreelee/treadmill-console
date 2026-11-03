import json,numpy as np,collections
d=json.load(open('matrix_dots.json'))
xs=sorted(set(round(p['x'],-1) for p in d))
# group by column using x clustering (gap 20)
d.sort(key=lambda p:p['x'])
cols=[[d[0]]]
for p in d[1:]:
    if p['x']-cols[-1][-1]['x']>20: cols.append([p])
    else: cols[-1].append(p)
print('columns',len(cols),'sizes',[len(c) for c in cols])
rowtab=collections.defaultdict(collections.Counter)
for c in cols:
    c.sort(key=lambda p:p['y'])
    for i,p in enumerate(c): rowtab[i][p['row']]+=1
print('row code by vertical order (0 = top):')
for i in sorted(rowtab): print(i,dict(rowtab[i]))
