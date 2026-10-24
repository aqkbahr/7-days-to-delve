"""Validate every new footprint, spawn, branch trail and campaign route sample."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'artifacts/maps/Allium-v0.3';n=8192
records=json.loads((p/'locations.json').read_text())
raw=np.memmap(p/'dtm.raw',dtype='<u2',mode='r',shape=(n,n))
water=Image.open(p/'splat4.png');biomes=Image.open(p/'biomes.png')
def px(x,z):return round(x+n//2),round(z+n//2)
for i,r in enumerate(records):
    x,y,z=r['position'];w,_,d=r['size'];cx,cz=px(x,z)
    footprint=raw[cz:cz+d+1,cx:cx+w+1].astype(float)/257
    assert np.max(np.abs(footprint-y))<.1,r['name']+' foundation'
    for other in records[:i]:
        a,_,b=other['position'];aw,_,ad=other['size']
        assert x+w<a or a+aw<x or z+d<b or b+ad<z,'Overlapping POIs'
    for x,z in r['access']:
        cx,cz=px(x,z); assert abs(raw[cz,cx]/257-y)<.2,r['name']+' access'
        assert water.getpixel((cx,n-1-cz))[2]==0
    a,b=np.array(r['access'][0]),np.array(r['access'][1])
    t=np.linspace(0,1,max(2,int(np.linalg.norm(b-a))))
    path=a[None,:]+t[:,None]*(b-a)[None,:]
    ix=np.rint(path[:,0]+n/2).astype(int);iz=np.rint(path[:,1]+n/2).astype(int)
    assert np.max(np.abs(raw[iz,ix].astype(float)/257-r['height']))<.2,r['name']+' branch surface'
for s in ET.parse(p/'spawnpoints.xml').getroot():
    x,y,z=map(float,s.attrib['position'].split(','));cx,cz=px(x,z)
    assert .5<y-raw[cz,cx]/257<4
    assert water.getpixel((cx,n-1-cz))[2]==0
    assert biomes.getpixel((cx,n-1-cz))==(0,64,0)
    for r in records:
        a,_,b=r['position'];w,_,d=r['size'];assert not(a-5<=x<=a+w+5 and b-5<=z<=b+d+5),'Spawn near POI'
spec=json.loads((ROOT/'src/Worlds/Allium/layout.json').read_text())
grades=[]
for route in [spec['route'],spec['capital_route']]:
    for a,b in zip(route,route[1:]):
        length=np.hypot(b[0]-a[0],b[1]-a[1])*n
        t=np.linspace(0,1,max(2,int(length/4)))
        xs=np.rint((a[0]+t*(b[0]-a[0]))*(n-1)).astype(int)
        zs=n-1-np.rint((a[1]+t*(b[1]-a[1]))*(n-1)).astype(int)
        heights=raw[zs,xs].astype(float)/257
        for r in records:
            x,_,z=r['position'];w,_,d=r['size']
            inside=(xs-n/2>=x-3)&(xs-n/2<=x+w+3)&(zs-n/2>=z-3)&(zs-n/2<=z+d+3)
            assert not inside.any(),r['name']+' blocks campaign trail'
        grades.extend(abs(np.diff(heights))/(length/(len(t)-1)))
assert max(grades)<.2,max(grades)
report={'result':'PASS','placements':len(records),'service_hubs':sum(r['service'] for r in records),
        'quest_tagged_exploration_sites':sum(bool(r['quest_tags']) and not r['service'] for r in records),
        'max_campaign_route_grade_percent':round(max(grades)*100,2),
        'checks':['all level foundations','no overlapping footprints','level branch trails and dry endpoints','dry forest spawns outside POIs','campaign route clear of building footprints','campaign route under 20% sampled grade'],
        'limits':'Does not validate rendered prefab access, quest availability or player traversal.'}
(p/'input-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
