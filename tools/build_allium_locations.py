"""Layer authored native POIs onto the v0.2 terrain, producing a NEW v0.3 world."""
import json, shutil, hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
spec=json.loads((ROOT/'src/Worlds/Allium/layout.json').read_text())
layout=json.loads((ROOT/'src/Worlds/Allium/locations.json').read_text())
source=ROOT/'artifacts/maps/Allium-v0.2'
out=ROOT/'artifacts/maps'/layout['world']
out.mkdir(parents=True,exist_ok=True)
native=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Prefabs/POIs')
n=8192
for name in ['biomes.png','splat1.png','splat2.png','radiation.png','spawnpoints.xml','water_info.xml']:
    shutil.copyfile(source/name,out/name)
h=np.fromfile(source/'dtm.raw',dtype='<u2').reshape(n,n)[::-1].astype(np.float32)/257
water=np.array(Image.open(source/'splat4.png'))
roads=np.array(Image.open(source/'splat3.png'))
biomes=Image.open(out/'biomes.png')
def pixel(x,z): return int(x+n//2),int(n//2-z-1)
def metadata(name):
    assert (native/(name+'.tts')).exists(),name
    return {e.attrib['name']:e.attrib.get('value') for e in ET.parse(native/(name+'.xml')).getroot().findall('property') if 'name' in e.attrib}
records=[]
for i,hub in enumerate(spec['sites']):
    x,y,z=hub['position']; wx,wz=round((x-.5)*n),round((.5-y)*n)
    # Keep the campaign trail outside trader walls. These quadrants are checked
    # against the sampled main route by the validator.
    dx,dz=[(-60,60),(60,-30),(-60,-30),(-60,60),(60,-30)][i]
    records.append({'name':hub['name'],'hub':i,'prefab':layout['hubs'][i], 'center':[wx+dx,wz+dz],'height':z,'service':True,'anchor':[wx,wz,z]})
for entry in layout['locations']:
    hub=spec['sites'][entry['hub']]; x,y,z=hub['position']; wx,wz=round((x-.5)*n),round((.5-y)*n)
    cx,cz=wx+entry['offset'][0],wz+entry['offset'][1]
    # Terraces share their hub elevation; access trails are then level and predictable.
    records.append(dict(entry,center=[cx,cz],height=z,service=False,anchor=[wx,wz,z]))
for r in records:
    props=metadata(r['prefab']); sx,sy,sz=map(int,props['PrefabSize'].split(','))
    cx,cz=r['center']; px,py=pixel(cx,cz)
    r.update(size=[sx,sy,sz],tier=int(props.get('DifficultyTier','0')),quest_tags=props.get('QuestTags',''),position=[cx-sx//2,r['height'],cz-sz//2])
    # Smooth square terrace, including an 8 m clear apron and 70 m transition.
    radius=max(sx,sz)//2+80
    yy,xx=np.mgrid[-radius:radius+1,-radius:radius+1]
    distance=np.maximum(np.abs(xx)-sx/2-8,np.abs(yy)-sz/2-8)
    weight=np.clip(1-distance/70,0,1); weight=weight*weight*(3-2*weight)
    view=h[py-radius:py+radius+1,px-radius:px+radius+1]
    view[:]=view*(1-weight)+r['height']*weight
    wview=water[py-radius:py+radius+1,px-radius:px+radius+1,2]
    wview[weight>0]=0
    assert biomes.getpixel((px,py))==tuple(spec['regions'][r['hub']]['game_rgb']),r['name']+' wrong biome'

# Branch paths end at each prefab's south edge and connect to the hub route node.
for r in records:
    cx,cz=r['center']; sx,_,sz=r['size']; ax,az,level=r['anchor']
    bx,bz=cx,cz-sz//2-5
    apx,apy=pixel(ax,az); bpx,bpy=pixel(bx,bz)
    left,right=min(apx,bpx)-24,max(apx,bpx)+25
    top,bottom=min(apy,bpy)-24,max(apy,bpy)+25
    yy,xx=np.mgrid[top:bottom,left:right]
    denom=(bpx-apx)**2+(bpy-apy)**2
    t=np.clip(((xx-apx)*(bpx-apx)+(yy-apy)*(bpy-apy))/max(1,denom),0,1)
    dist=np.hypot(xx-(apx+t*(bpx-apx)),yy-(apy+t*(bpy-apy)))
    weight=np.clip((22-dist)/16,0,1);weight=weight*weight*(3-2*weight)
    view=h[top:bottom,left:right];view[:]=view*(1-weight)+level*weight
    water[top:bottom,left:right,2][weight>0]=0
    roads[top:bottom,left:right,1][dist<=3]=255
    r['access']=[[ax,az],[bx,bz]]

# Final flattening protects foundations from neighboring trail blends.
for r in records:
    x,level,z=r['position'];sx,_,sz=r['size']
    px,py=pixel(x,z+sz)
    h[py-3:py+sz+5,px-3:px+sx+5]=level
    water[py-3:py+sz+5,px-3:px+sx+5,2]=0
    # Leave prefab-authored surfaces intact within the footprint.
    roads[py:py+sz+1,px:px+sx+1,:]=0

encoded=np.rint(h*257).astype('<u2')
encoded[::-1].tofile(out/'dtm.raw')
Image.fromarray(water).save(out/'splat4.png');Image.fromarray(roads).save(out/'splat3.png')
info=ET.parse(source/'map_info.xml');info.getroot().find("property[@name='Name']").set('value',layout['world']);info.write(out/'map_info.xml',encoding='utf-8',xml_declaration=True)
prefabs=ET.Element('prefabs')
for r in records:
    ET.SubElement(prefabs,'decoration',type='model',name=r['prefab'],position=','.join(map(str,r['position'])),rotation='0',y_is_groundlevel='true')
ET.indent(prefabs);ET.ElementTree(prefabs).write(out/'prefabs.xml',encoding='utf-8',xml_declaration=True)
(out/'locations.json').write_text(json.dumps(records,indent=2))
# Compact atlas: five local maps showing actual footprints, trails and labels.
atlas=Image.new('RGB',(1500,1050),'#17232b');draw=ImageDraw.Draw(atlas)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
colors=['#557e43','#645349','#ba8952','#bccfd7','#7b6788']
draw.text((25,16),'ALLIUM 0.3 / HUBS AND EXPLORATION SITES / NORTH UP',font=font,fill='white')
for i,hub in enumerate(spec['sites']):
    ox=25+(i%3)*495;oy=60+(i//3)*485
    draw.rectangle((ox,oy,ox+465,oy+450),fill=colors[i])
    draw.text((ox+12,oy+10),hub['name'],font=font,fill='white',stroke_width=1,stroke_fill='black')
    x,y,_=hub['position'];wx,wz=round((x-.5)*n),round((.5-y)*n)
    def local(x,z):return (ox+230+(x-wx)*.45,oy+260-(z-wz)*.45)
    for j,r in enumerate(records):
        if r['hub']!=i:continue
        draw.line([local(*p) for p in r['access']],fill='#ead197',width=3)
        x,_,z=r['position'];sx,_,sz=r['size'];a=local(x,z+sz);b=local(x+sx,z)
        draw.rectangle((*a,*b),fill='#f6d28d' if r['service'] else '#313841',outline='white')
        cx,cy=local(*r['center']);draw.text((cx+18,cy),str(j+1),font=font,fill='white',stroke_width=1,stroke_fill='black')
    rows=[(j,r) for j,r in enumerate(records) if r['hub']==i]
    for line,(j,r) in enumerate(rows):draw.text((ox+10,oy+365+line*19),f"{j+1}. {r['name']}"[:55],font=small,fill='white',stroke_width=1,stroke_fill='black')
draw.text((1020,590),'5 temporary trader hubs\n15 exploration locations\nNative placeholder structures\nLevel foundations + branch trails\nNew save required',font=font,fill='white',spacing=12)
atlas.save(out/'locations-atlas.png')
print(f'Built {len(records)} placements in {out}')
