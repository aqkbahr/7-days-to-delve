"""Independent checks for footprints, metadata, inherited content and dependencies."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as E
import numpy as np
from PIL import Image
from build_forest_delves import ROOT,SRC,OUT,DEST,NATIVE,props

new=json.loads((OUT/'dungeons.json').read_text());old=json.loads((SRC/'locations.json').read_text())
assert len(new)==4 and sorted(r['tier'] for r in new)==[1,1,2,2]
assert len(json.loads((OUT/'locations.json').read_text()))==len(old)+4
nodes=list(E.parse(OUT/'prefabs.xml').getroot());oldnodes=list(E.parse(SRC/'prefabs.xml').getroot())
assert [p.attrib for p in nodes[:len(oldnodes)]]==[p.attrib for p in oldnodes]
assert len(nodes)==len(oldnodes)+4
for name in ['biomes.png','splat1.png','splat2.png','splat4.png','spawnpoints.xml','water_info.xml','radiation.png','resource-sites.json']:
    assert hashlib.sha256((SRC/name).read_bytes()).digest()==hashlib.sha256((OUT/name).read_bytes()).digest(),name
h=np.memmap(OUT/'dtm.raw',dtype='<u2',mode='r',shape=(8192,8192))[::-1]
oldh=np.memmap(SRC/'dtm.raw',dtype='<u2',mode='r',shape=(8192,8192))[::-1]
biome=np.asarray(Image.open(OUT/'biomes.png').convert('RGB'));water=np.asarray(Image.open(OUT/'splat4.png'))[:,:,2]
roads=np.asarray(Image.open(OUT/'splat3.png'))[:,:,1]
for r in old:
    x,_,z=r['position'];sx,_,sz=r['size'];x+=4096;y=4095-z-sz
    assert np.array_equal(h[y-5:y+sz+6,x-5:x+sx+6],oldh[y-5:y+sz+6,x-5:x+sx+6])
for r in new:
    x,ground,z=r['position'];sx,sy,sz=r['size'];ix=x+4096;iy=4095-z-sz
    assert np.all(h[iy:iy+sz+1,ix:ix+sx+1]==ground*257)
    assert np.all(biome[iy:iy+sz+1,ix:ix+sx+1]==[0,64,0])
    assert not water[iy-10:iy+sz+11,ix-10:ix+sx+11].any()
    assert ground+r['yoffset']>=10
    for other in old+new:
        if other is r:continue
        xx,_,zz=other['position'];w,_,d=other['size']
        assert not(x<xx+w and x+sx>xx and z<zz+d and z+sz>zz)
    native=E.parse(NATIVE/(r['source']+'.xml')).getroot();converted=E.parse(DEST/(r['prefab']+'.xml')).getroot()
    def canon(e):return e.tag,sorted(e.attrib.items()),[canon(c) for c in e]
    for p in native:
        if p.get('name') in ['QuestTags','EditorGroups','ExcludeDistantPOIMesh']:continue
        other=next(c for c in converted if c.get('name')==p.get('name') and c.get('class')==p.get('class'))
        assert canon(p)==canon(other),(r['name'],p.attrib)
    tags=props(DEST/(r['prefab']+'.xml'))['QuestTags'];assert 'clear' in tags and 'fetch' in tags and 'restore_power' not in tags
    start,end=r['access'];distance=np.hypot(end[0]-start[0],end[1]-start[1]);steps=int(distance)+2
    xs=np.rint(np.linspace(start[0],end[0],steps)).astype(int)+4096
    ys=4095-np.rint(np.linspace(start[1],end[1],steps)).astype(int)
    assert not water[ys,xs].any() and roads[ys,xs].all()
    assert np.all(biome[ys,xs]==[0,64,0])
print('PASS: four full underground footprints; native quest/encounter metadata; all prior placements, gardens, ore metadata, water and starts preserved.')
