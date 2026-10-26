"""Grade approach terrain to the existing POI surface; preserve every POI position.

The alternative whole-POI lift would relocate saved quests, trader data and storage.
This candidate changes only the exterior eight-metre apron, keeping the interior
and all placement/quest coordinates intact. Saved columns require a native audit.
"""
from pathlib import Path
import csv,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];src=ROOT/'artifacts/maps/Allium-v0.10';out=ROOT/'artifacts/batch-02/apron-candidate';out.mkdir(exist_ok=True,parents=True)
records=json.loads((src/'locations.json').read_text());audit={r['prefab']:float(r['medianSurfaceDelta']) for r in csv.DictReader((ROOT/'artifacts/batch-02/poi-height-audit.csv').open()) if r['medianSurfaceDelta']!='NA'}
height=np.fromfile(src/'dtm.raw',dtype='<u2').reshape(8192,8192);original=height.copy();protected=np.zeros(height.shape,dtype=bool);boxes=[]
for r in records:
    x,y,z=r['position'];sx,sy,sz=r['size'];x+=4096;z+=4096;protected[z:z+sz,x:x+sx]=True;boxes.append((r,x,z,sx,sz))
rows=[]
for r,x,z,sx,sz in boxes:
    a,b,c,d=x-8,z-8,x+sx+8,z+sz+8;yy,xx=np.mgrid[b:d,a:c]
    dist=np.maximum.reduce([x-xx,xx-(x+sx-1),z-yy,yy-(z+sz-1)]).astype(float)
    w=np.clip((8-dist)/7,0,1);w=w*w*(3-2*w)
    delta=audit[r['prefab']];assert -2.1<delta<-.9
    mask=(dist>0)&(~protected[b:d,a:c]);before=original[b:d,a:c].astype(float)
    target=np.rint(before+delta*257*w).astype('<u2');part=height[b:d,a:c]
    part[mask]=np.minimum(part[mask],target[mask]);rows.append(dict(prefab=r['prefab'],position=r['position'],size=r['size'],delta=delta))
assert np.array_equal(height[protected],original[protected]);changed=height!=original
height.tofile(out/'dtm.raw')
# Compact exact column plan allows the native save repair to reject modified terrain.
zs,xs=np.nonzero(changed)
with (out/'columns.bin').open('wb') as f:
    data=np.empty(len(xs),dtype=[('x','<i4'),('z','<i4'),('old','<u2'),('new','<u2')]);data['x']=xs-4096;data['z']=zs-4096;data['old']=original[zs,xs];data['new']=height[zs,xs];f.write(data.tobytes())
report=dict(status='STAGED_REQUIRES_NATIVE_SAVE_VALIDATION',pois=len(rows),changed_columns=int(changed.sum()),max_lowering=float(((original.astype(float)-height)/257).max()),preserves_poi_positions=True,preserves_all_interior_height_samples=True,source_sha256=hashlib.sha256(original.tobytes()).hexdigest(),candidate_sha256=hashlib.sha256(height.tobytes()).hexdigest(),sites=rows)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='sites'})
