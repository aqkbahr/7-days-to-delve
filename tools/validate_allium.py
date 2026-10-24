"""Validate exported terrain data and the intended campaign walking corridor."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'artifacts/maps/Allium-v0.1'
spec=json.loads((ROOT/'src/Worlds/Allium/layout.json').read_text())
manifest=json.loads((out/'manifest.json').read_text())
n=manifest['size']
raw=np.memmap(out/'dtm.raw',dtype='<u2',mode='r',shape=(n,n))
png=np.asarray(Image.open(out/'heightmap.png'))
assert raw.nbytes==n*n*2
assert np.array_equal(png[::31,::29],raw[::-1][::31,::29]), 'Raw/PNG orientation or encoding mismatch'
assert png.min()>0 and png.max()<65535
biomes=Image.open(out/'biomes.png')
assert biomes.size==(n,n)
assert {rgb for count,rgb in biomes.getcolors(n*n)}=={tuple(r['game_rgb']) for r in spec['regions']}
grades=[]
for route in [spec['route'],spec['capital_route']]:
    for a,b in zip(route,route[1:]):
        distance=np.hypot(b[0]-a[0],b[1]-a[1])*n
        t=np.linspace(0,1,max(2,int(distance/8)))
        px=np.round((a[0]+t*(b[0]-a[0]))*(n-1)).astype(int)
        py=np.round((a[1]+t*(b[1]-a[1]))*(n-1)).astype(int)
        heights=png[py,px].astype(float)/257
        assert heights.min()>55,'Route crosses planned sea level'
        grades.extend(np.abs(np.diff(heights))/(distance/(len(t)-1)))
assert max(grades)<.2, f'Campaign route exceeds 20% grade: {max(grades)}'
for i,s in enumerate(spec['sites']):
    x,y,z=s['position']; px,py=round(x*(n-1)),round(y*(n-1))
    assert abs(float(png[py,px])/257-z)<.1
    assert biomes.getpixel((px,py))==tuple(spec['regions'][i]['game_rgb']),s['name']
report={'result':'PASS','size':n,'max_sampled_route_grade_percent':round(max(grades)*100,2),
        'checks':['raw byte size','PNG/raw sample equivalence with north/south flip','height range',
                  'exact five native biome colors','five site heights and biomes','route elevation and grade'],
        'limits':'Data checks only. No in-game loading, water, vegetation, POIs or player traversal validation.'}
(out/'validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
