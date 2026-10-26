"""Add guaranteed, marked native-block mineral deposits without changing terrain."""
from pathlib import Path
import collections, hashlib, json, random, shutil
import xml.etree.ElementTree as E
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'artifacts/maps/Allium-v0.6'; out=ROOT/'artifacts/maps/Allium-v0.7'
out.mkdir(parents=True,exist_ok=True)
author=ROOT/'playtest/OreAuthor/Mods'
report=E.parse(author/'AlliumTools/ore-build-report.xml')
assert len(report.getroot())==5
names=['iron','coal','lead','nitrate','shale']
dest=ROOT/'src/DelveWayrest/Prefabs/POIs'
for name in names:
    for ext in ('.tts','.xml','.blocks.nim'):
        p=author/'DelveWayrest/Prefabs/POIs'/('delve_ore_'+name+ext)
        assert p.exists() and p.stat().st_size
        shutil.copy2(p,dest/p.name)
for p in src.iterdir():
    if p.is_file() and p.name!='main.ttw':shutil.copy2(p,out/p.name)

h=np.memmap(src/'dtm.raw',dtype='<u2',mode='r',shape=(8192,8192))
biomes=Image.open(src/'biomes.png').convert('RGB')
water=np.asarray(Image.open(src/'splat4.png'))[:,:,2]
roads=np.asarray(Image.open(src/'splat3.png'))[:,:,1]
records=json.loads((src/'locations.json').read_text())
layout=json.loads((ROOT/'src/Worlds/Allium/layout.json').read_text())
regions=layout['regions']; colors={tuple(r['game_rgb']):i for i,r in enumerate(regions)}
rng=random.Random(74219)
sites=[]; candidates=collections.defaultdict(list)

def eligible(x,z):
    ix,iz=x+4096,z+4096;py=8191-iz
    if not(60<ix<8132 and 60<iz<8132):return None
    a=h[iz-7:iz+8,ix-7:ix+8].astype(float)/257
    if a.min()<60 or a.max()-a.min()>1.2:return None
    if water[py-25:py+26,ix-25:ix+26].any() or roads[py-25:py+26,ix-25:ix+26].any():return None
    region=colors.get(biomes.getpixel((ix,py)))
    if region is None:return None
    if any(biomes.getpixel((ix+dx,py+dz))!=tuple(regions[region]['game_rgb']) for dx,dz in [(-8,-8),(-8,8),(8,-8),(8,8)]):return None
    for r in records:
        px,_,pz=r['position'];w,_,d=r['size']
        if px-40<=x<=px+w+40 and pz-40<=z<=pz+d+40:return None
    for spawn in spawns:
        if (spawn[0]-x)**2+(spawn[2]-z)**2<60**2:return None
    return region,round(float(h[iz,ix])/257)

spawns=[list(map(float,p.get('position').split(','))) for p in E.parse(src/'spawnpoints.xml').getroot()]
for z0 in range(-3700,3701,320):
    for x0 in range(-3700,3701,320):
        for attempt in range(30):
            x=x0+rng.randrange(-80,81);z=z0+rng.randrange(-80,81)
            valid=eligible(x,z)
            if valid is not None:
                region,y=valid;candidates[region].append((x,y,z));break

for region in range(5):
    pool=candidates[region]
    assert len(pool)>=12,(regions[region]['name'],len(pool))
    hub=next(r for r in records if r['hub']==region and r['service'])
    hx,hz=hub['center'];pool.sort(key=lambda p:(p[0]-hx)**2+(p[2]-hz)**2)
    count=5 if region==2 else 4
    # Closest deposits include each regional mineral, so the town has a useful catchment.
    near=pool[:count];rest=pool[count:];rng.shuffle(rest)
    for i,(x,y,z) in enumerate(near+rest):
        k=i%count
        assert all((x-r['x'])**2+(z-r['z'])**2>=120**2 for r in sites)
        sites.append(dict(resource=names[k],index=k,region=regions[region]['name'],region_index=region,
                          x=x,y=y,z=z,prefab='delve_ore_'+names[k],nearest_town=hub['name']))
    if region==0:
        assert all((x-hx)**2+(z-hz)**2<1100**2 for x,y,z in near),'Starter deposits too distant'

tree=E.parse(src/'prefabs.xml')
for s in sites:E.SubElement(tree.getroot(),'decoration',type='model',name=s['prefab'],position=f"{s['x']-6},{s['y']},{s['z']-6}",rotation='0',y_is_groundlevel='true')
E.indent(tree);tree.write(out/'prefabs.xml',encoding='utf-8',xml_declaration=True)
tree=E.parse(src/'map_info.xml');tree.find("property[@name='Name']").set('value','Allium-v0.7');tree.write(out/'map_info.xml',encoding='utf-8',xml_declaration=True)
(out/'resource-sites.json').write_text(json.dumps(sites,indent=2))
(ROOT/'src/Worlds/Allium/resource-sites.json').write_text(json.dumps(sites,indent=2))
shutil.copy2(author/'AlliumTools/ore-build-report.xml',out/'ore-build-report.xml')

# An audit for every authored deposit, not just the locations sampled in runtime.
for s in sites:
    assert eligible(s['x'],s['z'])==(s['region_index'],s['y'])
    assert s['y']-22>3
    meta=E.parse(dest/(s['prefab']+'.xml')).getroot()
    assert meta.find("property[@name='CopyAirBlocks']").get('value').lower()=='false'
    assert meta.find("property[@name='YOffset']").get('value')=='-22'
for name in ['dtm.raw','biomes.png','splat1.png','splat2.png','splat3.png','splat4.png','radiation.png','spawnpoints.xml','water_info.xml']:
    assert hashlib.sha256((src/name).read_bytes()).digest()==hashlib.sha256((out/name).read_bytes()).digest()
summary={r['name']:dict(collections.Counter(s['resource'] for s in sites if s['region_index']==i)) for i,r in enumerate(regions)}
validation=json.loads((src/'input-validation.json').read_text())
validation.update(world='Allium-v0.7',placements=32+len(sites),gameplay_pois=32,guaranteed_mineral_deposits=len(sites),mineral_distribution=summary)
validation['checks']+=['Every authored mineral site avoids water, roads, POIs and player starts',
    'All five regions contain iron, coal, lead and nitrate; Drylands also contains shale',
    'Native marker over connected native ore; CopyAirBlocks false preserves surrounding terrain',
    'All original terrain inputs and 32 gameplay POI placements preserved']
(out/'input-validation.json').write_text(json.dumps(validation,indent=2))
pixels=np.array(biomes.resize((1024,1024),Image.Resampling.NEAREST))
original_pixels=pixels.copy()
for r in regions:pixels[np.all(original_pixels==r['game_rgb'],axis=2)]=r['preview_rgb']
pixels[water[::8,::8]>0]=(43,83,105)
pixels[(roads[::8,::8]>0)&(water[::8,::8]==0)]=(202,182,141)
im=Image.fromarray(pixels);d=ImageDraw.Draw(im)
palette=['#ed7d31','#222222','#40ccd1','#eeeeee','#ee74e5']
for s in sites:
    x=(s['x']+4096)/8;y=(4095-s['z'])/8
    d.ellipse((x-3,y-3,x+3,y+3),fill=palette[s['index']],outline='#000000')
d.rectangle((0,0,1024,48),fill='#17252c')
d.text((12,8),'ALLIUM RESOURCE AUDIT - GUARANTEED DEPOSITS (natural ore also remains)',fill='white')
d.text((12,27),'Orange: iron | Black: coal | Cyan: lead | White: nitrate | Pink: shale',fill='white')
for r in records:
    if not r['service']:continue
    x=(r['center'][0]+4096)/8;y=(4095-r['center'][1])/8
    d.rectangle((x-4,y-4,x+4,y+4),outline='white',width=2)
    d.text((x+7,y-4),r['name'],fill='white',stroke_width=2,stroke_fill='#17252c')
im.save(out/'resource-atlas.png')
print(json.dumps(dict(deposits=len(sites),regions=summary),indent=2))
