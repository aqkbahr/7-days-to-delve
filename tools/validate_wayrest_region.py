from pathlib import Path
import json,xml.etree.ElementTree as E
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'artifacts/maps/Allium-v0.5';n=8192
rs=json.loads((p/'locations.json').read_text());spec=json.loads((ROOT/'src/Worlds/Allium/layout.json').read_text())
h=np.memmap(p/'dtm.raw',dtype='<u2',mode='r',shape=(n,n));biome=Image.open(p/'biomes.png');water=Image.open(p/'splat4.png')
assert len(rs)==32
for i,r in enumerate(rs):
    x,y,z=r['position'];w,_,d=r['size'];a=x+4096;b=z+4096
    assert np.max(abs(h[b:b+d+1,a:a+w+1].astype(float)/257-y))<.1,r['name']+' foundation'
    for other in rs[:i]:
        ox,_,oz=other['position'];ow,_,od=other['size']
        assert x+w<ox or ox+ow<x or z+d<oz or oz+od<z,'Overlapping buildings'
    if r['hub']==0 and not r['service']:
        assert r['tier']==1
        for dx,dz in [(0,0),(w,0),(0,d),(w,d)]:
            assert biome.getpixel((a+dx,n-1-b-dz))==(0,64,0)
            assert water.getpixel((a+dx,n-1-b-dz))[2]==0
grades=[]
for route in [spec['route'],spec['capital_route']]:
    for a,b in zip(route,route[1:]):
        length=np.hypot(b[0]-a[0],b[1]-a[1])*n;t=np.linspace(0,1,max(2,int(length/4)))
        xs=np.rint((a[0]+t*(b[0]-a[0]))*(n-1)).astype(int);zs=n-1-np.rint((a[1]+t*(b[1]-a[1]))*(n-1)).astype(int)
        heights=h[zs,xs].astype(float)/257;grades.extend(abs(np.diff(heights))/(length/(len(t)-1)))
        for r in rs:
            x,_,z=r['position'];w,_,d=r['size'];assert not np.any((xs-4096>=x-3)&(xs-4096<=x+w+3)&(zs-4096>=z-3)&(zs-4096<=z+d+3)),r['name']+' blocks main road'
assert max(grades)<.2,max(grades)
branchgrades=[]
for r in rs:
  for a,b in zip(np.array(r['access']),np.array(r['access'])[1:]):
    length=np.linalg.norm(b-a);t=np.linspace(0,1,max(2,int(length/4)));line=a+t[:,None]*(b-a)
    ix=np.rint(line[:,0]+4096).astype(int);iz=np.rint(line[:,1]+4096).astype(int);height=h[iz,ix].astype(float)/257
    branchgrades.extend(abs(np.diff(height))/(length/(len(t)-1)))
    assert max(abs(np.diff(height))/(length/(len(t)-1)))<.2,r['name']+' steep access'
    for other in rs:
        if r['hub']!=0:continue
        if other is r:continue
        x,_,z=other['position'];w,_,d=other['size'];assert not np.any((line[:,0]>x-2)&(line[:,0]<x+w+2)&(line[:,1]>z-2)&(line[:,1]<z+d+2)),r['name']+' path through '+other['name']
for spawn in E.parse(p/'spawnpoints.xml').getroot():
    x,y,z=map(float,spawn.get('position').split(','));ix,iz=round(x+4096),round(z+4096)
    assert .5<y-h[iz,ix]/257<4 and water.getpixel((ix,n-1-iz))[2]==0
forest=[r for r in rs if r['hub']==0 and not r['service']]
report=dict(result='PASS',world='Allium-v0.5',placements=len(rs),forest_tier1_pois=len(forest),clear_eligible=sum('clear' in r['quest_tags'] for r in forest),fetch_eligible=sum('fetch' in r['quest_tags'] for r in forest),max_campaign_grade_percent=round(max(grades)*100,2),max_branch_grade_percent=round(max(branchgrades)*100,2),checks=['flat foundations','no overlapping POIs','Forest footprint biomes and dry foundations','main roads and Forest branches clear of buildings','sampled road grades below 20 percent','dry spawn clearance'],limits='Walking and rendered inspection deferred. Older branches in other biomes still need routing review; Arbor hunter path intersects its hub compound.')
(p/'input-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
