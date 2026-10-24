"""Check native world inputs before spending time loading them in game."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'artifacts/maps/Allium-v0.2'
n=8192
raw=np.memmap(p/'dtm.raw',dtype='<u2',mode='r',shape=(n,n))
water=Image.open(p/'splat4.png')
biome=Image.open(p/'biomes.png')
roads=Image.open(p/'splat3.png')
for name in ['splat1.png','splat2.png','splat3.png','splat4.png','biomes.png']:
    assert Image.open(p/name).size==(n,n),name
def pixel(x,z): return round(x+n/2),round(n/2-z)-1
for spawn in ET.parse(p/'spawnpoints.xml').getroot():
    x,y,z=map(float,spawn.attrib['position'].split(',')); px,py=pixel(x,z)
    h=raw[n-1-py,px]/257
    assert 0.5<y-h<4,(h,y)
    assert water.getpixel((px,py))[2]==0
    assert biome.getpixel((px,py))==(0,64,0)
    area=raw[n-1-py-3:n-1-py+4,px-3:px+4].astype(float)/257
    assert np.ptp(area)<1,'Uneven spawn site'
assert water.getpixel((int(.575*n),int(.51*n)))[2]==50,'Lake missing'
assert water.getpixel((60,60))[2]==50,'Ocean missing'
assert roads.getextrema()[1][1]==255 and roads.getextrema()[2][1]==0
for poi in ET.parse(p/'prefabs.xml').getroot():
    name=poi.attrib['name']
    native=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Prefabs/POIs')
    props={v.attrib['name']:v.attrib.get('value') for v in ET.parse(native/(name+'.xml')).getroot().findall('property') if 'name' in v.attrib}
    assert (native/(name+'.tts')).exists()
    x,y,z=map(int,poi.attrib['position'].split(','))
    width,_,depth=map(int,props['PrefabSize'].split(','))
    for dx,dz in [(0,0),(width,0),(0,depth),(width,depth)]:
        px,py=pixel(x+dx,z+dz)
        assert abs(raw[n-1-py,px]/257-y)<.2,'POI footprint not flat'
report={'result':'PASS','checks':['4 dry, flat forest spawn positions','native image sizes','lake and ocean water','gravel road channel','native prefab exists and footprint fits level terrain'], 'limits':'Runtime validation is recorded separately; does not prove player traversal or water simulation stability.'}
(p/'input-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
