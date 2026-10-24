"""Build Allium's editable terrain blockout. Requires numpy and Pillow.

This exports terrain authoring assets, not a complete installable game world.
Coordinates in the specification are normalized, north at image top.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]

def build(size=8192):
    spec = json.loads((ROOT / 'src/Worlds/Allium/layout.json').read_text())
    out = ROOT / 'artifacts/maps/Allium-v0.1'
    out.mkdir(parents=True, exist_ok=True)
    n = 1024
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) / (n-1)
    rng = np.random.default_rng(spec['seed'])
    def noise(k):
        a = rng.random((k,k), dtype=np.float32)
        return np.asarray(Image.fromarray(a).resize((n,n), Image.Resampling.BICUBIC)) - .5
    broad, fine = noise(14), noise(70)
    def mask(points):
        im = Image.new('L',(n,n))
        ImageDraw.Draw(im).polygon([(int(a*(n-1)),int(b*(n-1))) for a,b in points],fill=255)
        return im
    land = mask(spec['coast'])
    coast = np.asarray(land.filter(ImageFilter.GaussianBlur(14)),dtype=np.float32)/255
    biome = np.zeros((n,n),dtype=np.uint8)
    for i, region in enumerate(spec['regions']):
        if 'polygon' in region:
            biome[np.asarray(mask(region['polygon']))>0] = i
    h = 62 + 17*broad + 5*fine
    def soft_region(i):
        return np.asarray(Image.fromarray(np.uint8(biome==i)*255).filter(ImageFilter.GaussianBlur(7)),dtype=np.float32)/255
    h += soft_region(1)*12 + soft_region(2)*(24+16*(broad+.5))
    # NW highlands and the diagonal mountain divide, with individually varied ridges.
    spine = np.exp(-((x-(.24+.65*y))/.055)**2)
    highlands = np.exp(-(((x-.23)/.25)**2+((y-.13)/.18)**2))
    ridges = .35 + .65*(1-np.clip(np.abs(noise(42))*2,0,1))**3
    h += 100*spine*ridges + 85*highlands*ridges
    h += soft_region(4)*22
    h = 24+(h-24)*coast
    # Central lake basin. Water surface is an authoring plan, not a game water file.
    lake = ((x-.575)/.043)**2+((y-.51)/.06)**2
    h = h*(1-np.clip(1.4-lake,0,1)) + 42*np.clip(1.4-lake,0,1)
    road = np.zeros_like(h)
    def corridor(points, width, carve=False):
        nonlocal h
        result = np.zeros_like(h)
        for a,b in zip(points,points[1:]):
            ax,ay,az=a; bx,by,bz=b
            t=np.clip(((x-ax)*(bx-ax)+(y-ay)*(by-ay))/((bx-ax)**2+(by-ay)**2),0,1)
            d=np.hypot(x-(ax+t*(bx-ax)),y-(ay+t*(by-ay)))
            w=np.clip((width*2-d)/width,0,1)
            w=w*w*(3-2*w)
            target=az+t*(bz-az)
            h=h*(1-w)+ (np.minimum(h,target) if carve else target)*w
            result=np.maximum(result,w)
        return result
    river = corridor(spec['river'],.003,True)
    road = corridor(spec['route'],.004)
    road = np.maximum(road, corridor(spec['capital_route'],.004))
    for site in spec['sites']:
        sx,sy,sz=site['position']
        d=np.hypot(x-sx,y-sy)*size
        w=np.clip((site['radius_m']+55-d)/55,0,1)
        w=w*w*(3-2*w)
        h=h*(1-w)+sz*w
    h=np.clip(h,8,240)
    # Float interpolation precedes integer encoding. PNG rows run north -> south.
    full=Image.fromarray(h.astype(np.float32)).resize((size,size),Image.Resampling.BILINEAR)
    encoded=np.round(np.asarray(full)*257).astype('<u2')
    Image.fromarray(encoded).save(out/'heightmap.png')
    # Native SaveHeightMapRAW uses height * 257; raw rows run south -> north.
    encoded[::-1].tofile(out/'dtm.raw')
    colors=np.array([r['game_rgb'] for r in spec['regions']],dtype=np.uint8)
    Image.fromarray(colors[biome]).resize((size,size),Image.Resampling.NEAREST).save(out/'biomes.png')
    for name, data in [('route-mask',road),('river-mask',river),('land-mask',coast)]:
        Image.fromarray(np.uint8(data*255)).resize((size,size),Image.Resampling.BILINEAR).save(out/(name+'.png'))
    # A shaded planning preview with actual terrain and reserved sites.
    palette=np.array([r['preview_rgb'] for r in spec['regions']],dtype=np.float32)
    gy,gx=np.gradient(h)
    shade=np.clip(.85 + .22*(-gx-gy),.45,1.2)
    rgb=np.clip(palette[biome]*shade[...,None],0,255)
    rgb[h<50]=[47,100,121]
    rgb[river>.6]=[62,133,157]
    rgb[road>.6]=[232,209,151]
    im=Image.fromarray(rgb.astype(np.uint8)); draw=ImageDraw.Draw(im)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
    for i,s in enumerate(spec['sites'],1):
        sx,sy,_=s['position']; px,py=int(sx*n),int(sy*n)
        draw.ellipse((px-8,py-8,px+8,py+8),fill='#ffe2a1',outline='#25221b',width=2)
        label=f"{i}. {s['name']}"
        box=draw.textbbox((px+13,py-10),label,font=font)
        draw.rectangle((box[0]-4,box[1]-3,box[2]+4,box[3]+3),fill='#222b30')
        draw.text((px+13,py-10),label,font=font,fill='white')
    draw.rectangle((0,0,n,40),fill='#18252c')
    draw.text((18,9),'ALLIUM / TERRAIN BLOCKOUT 0.1 / 8 KM / NORTH UP',font=font,fill='white')
    draw.rectangle((0,n-42,n,n),fill='#18252c')
    draw.text((18,n-31),'Forest | Burnt Arbor | Drylands | Snow Highlands | Queen\'s Reach    -    Buildings and water pending',font=small,fill='white')
    im.save(out/'preview.png')
    sites=[]
    for s in spec['sites']:
        sx,sy,sz=s['position']
        sites.append(dict(s,world_xyz=[round((sx-.5)*size),sz,round((.5-sy)*size)]))
    (out/'sites.json').write_text(json.dumps(sites,indent=2))
    report={'size':size,'seed':spec['seed'],'height_range_m':[float(h.min()),float(h.max())],
            'status':'Terrain blockout; NOT an installable or runtime-validated world',
            'raw_encoding':'little-endian uint16; height * 257; south-first rows',
            'png_encoding':'uint16; height * 257; north-first rows',
            'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file() and p.name!='manifest.json'}}
    (out/'manifest.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--size',type=int,default=8192,choices=[2048,4096,8192])
    build(parser.parse_args().size)
