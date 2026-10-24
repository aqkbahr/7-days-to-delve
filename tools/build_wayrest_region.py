"""Add a varied Forest contract district to a new v0.5 map, preserving v0.4."""
from pathlib import Path
import json,shutil,xml.etree.ElementTree as E
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];n=8192
src=ROOT/'artifacts/maps/Allium-v0.4';out=ROOT/'artifacts/maps/Allium-v0.5';out.mkdir(parents=True,exist_ok=True)
for name in ['biomes.png','splat1.png','splat2.png','radiation.png','spawnpoints.xml','water_info.xml','wayrest-plan.png']:shutil.copyfile(src/name,out/name)
h=np.fromfile(src/'dtm.raw',dtype='<u2').reshape(n,n)[::-1].astype(np.float32)/257
water=np.array(Image.open(src/'splat4.png'));roads=np.array(Image.open(src/'splat3.png'));biome=Image.open(src/'biomes.png')
records=json.loads((src/'locations.json').read_text());spec=json.loads((ROOT/'src/Worlds/Allium/layout.json').read_text())
native=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Prefabs/POIs')
def pixel(x,z):return int(x+4096),int(4095-z)
route=[]
for a,b in zip(spec['route'][:5],spec['route'][1:5]):
    for t in np.linspace(0,1,100):route.append([(a[0]+t*(b[0]-a[0])-.5)*n,(.5-a[1]-t*(b[1]-a[1]))*n,a[2]+t*(b[2]-a[2])])
route=np.array(route)
choices=[('cabin_05','Forager cottage'),('cabin_06','Woodcutter refuge'),('cabin_07','Abandoned hunting lodge'),('cabin_08','Fernwood homestead'),('cabin_10','Hillside cottage'),('cabin_12','Old forester house'),('cabin_14','Mosswood cabin'),('farm_12','Border farm'),('oldwest_business_01','Forest trading post'),('oldwest_business_08','Roadside provisioner'),('oldwest_church','Woodland chapel'),('ranger_station_05','Forest watch')]
new=[]
# Select dry locations on both sides of the campaign road. A trail cannot cut
# through another building, a river, or a biome boundary.
candidates=[(x,z) for x in range(-2400,-1150,175) for z in range(-2450,-1599,170)]
for prefab,name in choices:
    p={e.get('name'):e.get('value') for e in E.parse(native/(prefab+'.xml')).getroot().findall('property')}
    sx,sy,sz=map(int,p['PrefabSize'].split(','));assert p['DifficultyTier']=='1'
    chosen=None
    for cx,cz in candidates:
        px,py=pixel(cx,cz);rad=max(sx,sz)//2+25
        if biome.getpixel((px,py))!=(0,64,0) or np.any(water[py-rad:py+rad+1,px-rad:px+rad+1,2]):continue
        if any(abs(cx-r['center'][0])<150 and abs(cz-r['center'][1])<150 for r in records+new):continue
        distances=np.hypot(route[:,0]-cx,route[:,1]-cz)
        if distances.min()<max(sx,sz)/2+25:continue
        ax,az,level=route[np.argmin(distances)]
        # South approach, with a straight branch checked for other buildings.
        bx,bz=cx,cz-sz//2-6
        t=np.linspace(0,1,max(2,int(np.hypot(bx-ax,bz-az))))
        xs=ax+t*(bx-ax);zs=az+t*(bz-az)
        ix=np.rint(xs+4096).astype(int);iy=np.rint(4095-zs).astype(int)
        if np.any(water[iy,ix,2]):continue
        if any(np.any((xs>r['position'][0]-12)&(xs<r['position'][0]+r['size'][0]+12)&(zs>r['position'][2]-12)&(zs<r['position'][2]+r['size'][2]+12)) for r in records+new):continue
        # Do not place a later building across an earlier branch.
        blocked=False
        for r in new:
            a,b=np.array(r['access']);tt=np.linspace(0,1,200);line=a+tt[:,None]*(b-a)
            if np.any((abs(line[:,0]-cx)<sx/2+12)&(abs(line[:,1]-cz)<sz/2+12)):blocked=True
        if blocked:continue
        chosen=(cx,cz,ax,az,round(level));break
    assert chosen is not None,'No safe placement for '+name
    cx,cz,ax,az,level=chosen;candidates.remove((cx,cz))
    r=dict(name=name,hub=0,prefab=prefab,center=[cx,cz],height=level,service=False,size=[sx,sy,sz],tier=1,quest_tags=p['QuestTags'],position=[cx-sx//2,level,cz-sz//2],access=[[float(ax),float(az)],[cx,cz-sz//2-6]])
    new.append(r)
for r in new:
    cx,cz=r['center'];sx,_,sz=r['size'];px,py=pixel(cx,cz);level=r['height'];rad=max(sx,sz)//2+70
    yy,xx=np.mgrid[-rad:rad+1,-rad:rad+1];d=np.maximum(abs(xx)-sx/2-5,abs(yy)-sz/2-5)
    blend=np.clip(1-d/60,0,1);blend=blend*blend*(3-2*blend)
    # Preserve actual water columns; all foundations are dry.
    blend[water[py-rad:py+rad+1,px-rad:px+rad+1,2]>0]=0
    v=h[py-rad:py+rad+1,px-rad:px+rad+1];v[:]=v*(1-blend)+level*blend
    a,b=r['access'];apx,apy=pixel(*a);bpx,bpy=pixel(*b)
    l,rr=min(apx,bpx)-20,max(apx,bpx)+21;top,bot=min(apy,bpy)-20,max(apy,bpy)+21
    yy,xx=np.mgrid[top:bot,l:rr];t=np.clip(((xx-apx)*(bpx-apx)+(yy-apy)*(bpy-apy))/max(1,(bpx-apx)**2+(bpy-apy)**2),0,1)
    d=np.hypot(xx-apx-t*(bpx-apx),yy-apy-t*(bpy-apy));w=np.clip((18-d)/12,0,1);w=w*w*(3-2*w)
    start=float(h[apy,apx]);target=start+t*(level-start)
    w[water[top:bot,l:rr,2]>0]=0
    v=h[top:bot,l:rr];v[:]=v*(1-w)+target*w;roads[top:bot,l:rr,1][d<=3]=255
# Correct the older cabin shortcut, which ran through Wayrest's compound.
r=records[5];r['access']=[[-2621,-2212],[-2811,-2212],[-2811,-2128]]
for a,b in zip(r['access'],r['access'][1:]):
    apx,apy=pixel(*a);bpx,bpy=pixel(*b)
    l,rr=min(apx,bpx)-20,max(apx,bpx)+21;top,bot=min(apy,bpy)-20,max(apy,bpy)+21
    yy,xx=np.mgrid[top:bot,l:rr];t=np.clip(((xx-apx)*(bpx-apx)+(yy-apy)*(bpy-apy))/max(1,(bpx-apx)**2+(bpy-apy)**2),0,1)
    d=np.hypot(xx-apx-t*(bpx-apx),yy-apy-t*(bpy-apy));w=np.clip((18-d)/12,0,1);w=w*w*(3-2*w)
    v=h[top:bot,l:rr];v[:]=v*(1-w)+65*w;roads[top:bot,l:rr,1][d<=3]=255
# Protect every footprint after blending and retain authored surfaces.
for r in records+new:
    x,y,z=r['position'];sx,_,sz=r['size'];px,py=pixel(x,z+sz)
    h[py-2:py+sz+4,px-2:px+sx+4]=y;roads[py:py+sz+1,px:px+sx+1,:]=0
np.rint(h*257).astype('<u2')[::-1].tofile(out/'dtm.raw')
Image.fromarray(roads).save(out/'splat3.png');Image.fromarray(water).save(out/'splat4.png')
tree=E.parse(src/'prefabs.xml')
for r in new:E.SubElement(tree.getroot(),'decoration',type='model',name=r['prefab'],position=','.join(map(str,r['position'])),rotation='0',y_is_groundlevel='true')
E.indent(tree);tree.write(out/'prefabs.xml',encoding='utf-8',xml_declaration=True)
tree=E.parse(src/'map_info.xml');tree.find("property[@name='Name']").set('value','Allium-v0.5');tree.write(out/'map_info.xml',encoding='utf-8',xml_declaration=True)
(out/'locations.json').write_text(json.dumps(records+new,indent=2))
(ROOT/'src/Worlds/Allium/wayrest-locations.json').write_text(json.dumps(new,indent=2))
im=Image.new('RGB',(1400,1000),'#1b3027');d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
def xy(x,z):return (60+(x+3000)*.6,60+(-1500-z)*.6)
d.text((30,15),'WAYREST / LIVING BORDER / NORTH UP / CONTRACT DISTRICT',font=font,fill='white')
d.line([xy(*p[:2]) for p in route],fill='#dbcba3',width=5)
local=[r for r in records+new if r['hub']==0]
for i,r in enumerate(local):
    x,y,z=r['position'];sx,_,sz=r['size'];d.rectangle((*xy(x,z+sz),*xy(x+sx,z)),fill='#d2a55d' if r['service'] else '#8eae74',outline='white')
    d.text(xy(*r['center']),str(i+1),font=font,fill='white',stroke_width=1,stroke_fill='black')
    if 'access' in r:d.line([xy(*p) for p in r['access']],fill='#b59c69',width=2)
d.rectangle((990,50,1399,900),fill='#1b3027')
for i,r in enumerate(local):d.text((1010,70+i*40),f"{i+1}. {r['name']}",font=font,fill='white')
d.text((30,940),'15 Tier 1 Forest POIs + Wayrest | 3 rotating contract types | Native structures, custom campaign',font=font,fill='white')
im.save(out/'locations-atlas.png')
print('Added',len(new),'Forest POIs; total',len(records+new))
