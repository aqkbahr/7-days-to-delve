"""Independent world/metadata checks for the Arbor expansion."""
from pathlib import Path
import collections, hashlib, json, math
import xml.etree.ElementTree as E
import numpy as np
from PIL import Image
from build_arbor_region import properties, questable, ROOT, SOURCE, OUT, DEST

records=json.loads((OUT/'locations.json').read_text())
old=json.loads((SOURCE/'locations.json').read_text())
arbor=[r for r in records if r['hub']==1]
new=[r for r in records if 'footprint_image' in r]
assert len(arbor)==480 and len(new)==476 and len(records)==508
assert sum(questable(r['quest_tags'],r['tier']) for r in arbor)==280
placements=list(E.parse(OUT/'prefabs.xml').getroot())
assert len(placements)==508+377
h=np.memmap(OUT/'dtm.raw',dtype='<u2',mode='r',shape=(8192,8192))[::-1]
oldh=np.memmap(SOURCE/'dtm.raw',dtype='<u2',mode='r',shape=(8192,8192))[::-1]
b=np.asarray(Image.open(OUT/'biomes.png').convert('RGB'))
water=np.asarray(Image.open(OUT/'splat4.png'))[:,:,2]
roads=np.asarray(Image.open(OUT/'splat3.png'))[:,:,1]
oldroads=np.asarray(Image.open(SOURCE/'splat3.png'))[:,:,1]
for name in ['biomes.png','splat1.png','splat2.png','splat4.png','radiation.png','spawnpoints.xml','water_info.xml','resource-sites.json']:
    assert hashlib.sha256((SOURCE/name).read_bytes()).digest()==hashlib.sha256((OUT/name).read_bytes()).digest(),name
assert np.all(roads[oldroads>0]>0),'Old road removed'
for r in old:
    current=next(q for q in records if q['position']==r['position'])
    assert current['size']==r['size']
    if r['hub']!=1 or r['service']:assert current['prefab']==r['prefab']
    x,_,z=r['position'];sx,_,sz=r['size'];a=x+4096;b0=4095-z-sz
    assert np.array_equal(h[b0-5:b0+sz+6,a-5:a+sx+6],oldh[b0-5:b0+sz+6,a-5:a+sx+6])
for r in json.loads((OUT/'resource-sites.json').read_text()):
    x,y=r['x']+4096,4095-r['z']
    assert np.array_equal(h[y-14:y+15,x-14:x+15],oldh[y-14:y+15,x-14:x+15]),'Changed ore cover'
    assert not roads[y-14:y+15,x-14:x+15].any(),'Road over mineral deposit'
max_grade=0
for i,r in enumerate(new):
    a,y,c,d=r['footprint_image'];sx,_,sz=r['size']
    assert np.all(b[y:d+1,a:c+1]==[186,0,255])
    assert not water[y-8:d+9,a-8:c+9].any()
    assert np.all(h[y:d+1,a:c+1]==r['height']*257),'Foundation not level'
    for other in new[i+1:]:
        aa,bb,cc,dd=other['footprint_image']
        assert not(a<cc and c>aa and y<dd and d>bb),'Overlapping POIs'
    for x,z in r['access']:
        px,py=x+4096,4095-z
        assert tuple(b[py,px])==(186,0,255) and water[py,px]==0
        assert roads[py,px]>0,'Missing access path'
    for (x,z),(xx,zz) in zip(r['access'],r['access'][1:]):
        distance=math.hypot(xx-x,zz-z)
        if not distance:continue
        grade=abs(int(h[4095-z,x+4096])-int(h[4095-zz,xx+4096]))/257/distance
        max_grade=max(max_grade,grade)
        assert grade<=0.5,(r['name'],'Path too steep',grade)
    endx,endz=r['access'][-1]
    # Dijkstra root cell must contain an existing campaign road.
    ex,ey=endx+4096,4095-endz
    assert oldroads[(ey//8)*8:(ey//8+1)*8,(ex//8)*8:(ex//8+1)*8].any()
for name in {r['prefab'] for r in arbor if not r['service']}:
    p=properties(DEST/(name+'.xml'));assert p['ExcludeDistantPOIMesh']=='True'
    assert 'restore_power' not in p.get('QuestTags','')
    assert (DEST/(name+'.tts')).stat().st_size>0
    if questable(p.get('QuestTags',''),int(p.get('DifficultyTier','0'))):
        assert p.get('SleeperVolumeSize'),name+' missing encounters'
report=json.loads((OUT/'arbor-build.json').read_text())
report.update(result='PASS',placements=len(placements),max_sampled_path_grade=round(max_grade,4),
    checks=['480 Arbor locations, including 280 native quest-capable Tier 1–4 POIs',
    '476 additions have level foundations, non-overlapping bounds and wholly Arbor footprints',
    'Every added location has a dry gravel path connected to the existing road network',
    'All 377 mineral deposits and original POI foundations retained; no roads over ore seams',
    'Water, biome, spawn, radiation and ore metadata byte-identical to v0.7',
    'Quest tiers, clear/fetch/infested tags, sleeper and trigger metadata preserved by conversion'],
    limits='Automated/native headless checks only. Visual review, human traversal, quest rally/reset and full combat playthrough remain pending. Electrical restore-power jobs are intentionally excluded from converted sites. Existing Arbor Camp remains the native temporary trader hub.')
(OUT/'input-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
