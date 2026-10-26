"""Deterministic Arbor settlement expansion using native-serialized fantasy variants.

Run --plan before native authoring, then without arguments to publish Allium-v0.8.
No generated saves or existing world revisions are overwritten.
"""
from pathlib import Path
import collections, csv, heapq, json, math, random, shutil, sys
import xml.etree.ElementTree as E
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
NATIVE = Path('D:/Steam/steamapps/common/7 Days To Die/Data/Prefabs/POIs')
SOURCE = ROOT/'artifacts/maps/Allium-v0.7'
OUT = ROOT/'artifacts/maps/Allium-v0.8'
WORK = ROOT/'artifacts/arbor'
AUTHOR = ROOT/'playtest/ArborAuthor/Mods'
DEST = ROOT/'src/DelveWayrest/Prefabs/POIs'

def properties(path):
    return {p.get('name'): p.get('value','') for p in E.parse(path).getroot()}

def questable(tags, tier):
    return tier > 0 and bool(set(tags.replace(' ','').split(',')) & {'clear','fetch','infested'})

def catalog():
    names=(WORK/'arbor-sources.txt').read_text().splitlines()
    titles={
        'oldwest_business_01':'Ashmarket Storehouse','oldwest_business_02':'Cinder Butchery',
        'oldwest_business_03':'Charcoal Row','oldwest_business_04':'Emberwright Workshop',
        'oldwest_business_05':'Abandoned Timber Shop','oldwest_business_06':'Ashen Counting House',
        'oldwest_business_07':'Deserted Provisioner','oldwest_business_08':'The Sooted Lantern Inn',
        'oldwest_business_09':'Empty Market Hall','oldwest_business_10':'Cinder Apothecary',
        'oldwest_business_11':'The Black Bough Tavern','oldwest_business_12':'Cooper’s Workshop',
        'oldwest_business_13':'Ashwood Guildhouse','oldwest_business_14':'Scorched Trading House',
        'oldwest_church':'Chapel of Embers','oldwest_gallows':'Ashen Gallows',
        'oldwest_jail':'Abandoned Watch House','oldwest_stables':'Deserted Stables',
        'remnant_church_01':'Ashwood Chapel Ruins','ranger_station_01':'Arbor Watch',
        'cemetery_01':'Cinder Burial Ground','cemetery_02':'Ashen Crypt',
        'rural_church_01':'Blackbough Sanctuary','rural_church_02':'Ember Parish',
    }
    prefixes=['Ashwood','Cinder','Blackbough','Ember','Sootfall','Greyroot','Charred Oak','Hollow Ash','Duskwood','Coalbrook']
    rows=[]
    for n in names:
        p=properties(NATIVE/(n+'.xml')); tier=int(p.get('DifficultyTier','0'))
        number=int(n.rsplit('_',1)[-1]) if n.rsplit('_',1)[-1].isdigit() else 1
        if n.startswith('cabin_'): title=prefixes[(number-1)%10]+' '+(['Woodcutter’s Cottage','Hunting Lodge','Forester’s House'][((number-1)//10)%3])
        elif n.startswith('farm_'):title=prefixes[(number-1)%10]+' '+(['Farmstead','Grange'][((number-1)//10)%2])
        elif n.startswith('remnant_burnt_'):title=prefixes[(number-1)%10]+' Burned Homestead'
        elif n.startswith('remnant_farm_'):title=prefixes[(number-1)%10]+' Abandoned Farm'
        elif n.startswith('remnant_oldwest_'):title=prefixes[(number-1)%10]+' Market Ruins'
        elif n.startswith('oldwest_strip_'):title=prefixes[(number-1)%10]+' Artisan Row'
        else:title=titles.get(n,n)
        tags=', '.join(t.strip() for t in p.get('QuestTags','').split(',') if t.strip() and t.strip()!='restore_power')
        rows.append(dict(source=n,prefab='delve_arbor_'+n,name=titles.get(n,title),
                         size=list(map(int,p['PrefabSize'].split(','))),tier=tier,
                         quest_tags=tags,questable=questable(tags,tier),yoffset=int(p.get('YOffset','0'))))
    (WORK/'catalog.json').write_text(json.dumps(rows,indent=2))
    return rows

def build():
    cat=catalog(); rng=random.Random(742198)
    records=json.loads((SOURCE/'locations.json').read_text())
    minerals=json.loads((SOURCE/'resource-sites.json').read_text())
    # Image coordinates throughout: world x = column-4096; z = 4095-row.
    h=np.fromfile(SOURCE/'dtm.raw',dtype='<u2').reshape(8192,8192)[::-1].copy()
    biome=np.asarray(Image.open(SOURCE/'biomes.png').convert('RGB'))
    water=np.asarray(Image.open(SOURCE/'splat4.png'))
    roads=np.array(Image.open(SOURCE/'splat3.png'))
    arbor=np.all(biome==[186,0,255],axis=2)
    del biome
    watermask=water[:,:,2]>0
    original_roads=roads[:,:,1]>0
    occupied=[]
    for r in records:
        x,_,z=r['position'];sx,_,sz=r['size']
        occupied.append((x+4096,4095-z-sz,x+4096+sx,4095-z))
    for m in minerals:
        px,py=m['x']+4096,4095-m['z'];occupied.append((px-14,py-14,px+14,py+14))
    def intersects(box,margin):
        a,b,c,d=box
        return any(a-margin<k and c+margin>i and b-margin<l and d+margin>j for i,j,k,l in occupied)
    # Nearer sites favour the camp and several hamlets; wilderness infill follows.
    seeds=[]
    for y in range(4700,7300,500):
        for x in range(3300,7400,500):
            x+=rng.randrange(-120,121);y+=rng.randrange(-120,121)
            if arbor[y,x] and h[y,x]>60*257 and not watermask[y,x]: seeds.append((x,y))
    candidates=[]
    for y in range(4200,8000,80):
        for x in range(3200,8000,80):
            px=x+rng.randrange(-21,22);py=y+rng.randrange(-21,22)
            if arbor[py,px]:candidates.append((px,py))
    rng.shuffle(candidates)
    candidates.sort(key=lambda v:min((v[0]-x)**2+(v[1]-y)**2 for x,y in seeds))
    existing_quests=sum(questable(r['quest_tags'],r['tier']) for r in records if r['hub']==1)
    # A middle-biome mix: more Tier 2/3 than the starter forest, a few Tier 4 farms.
    tier_targets={1:140,2:100,3:33,4:5}
    assert sum(tier_targets.values())==280-existing_quests
    jobs=[]
    for tier,count in tier_targets.items():
        pool=[r for r in cat if r['questable'] and r['tier']==tier]
        assert pool,(tier,'no source')
        rng.shuffle(pool)
        jobs.extend(pool[i%len(pool)] for i in range(count))
    pool=[r for r in cat if not r['questable'] and r['source']!='oldwest_stables']
    rng.shuffle(pool);jobs.extend(pool[i%len(pool)] for i in range(480-4-len(jobs)))
    rng.shuffle(jobs)
    # Largest foundations first so small ruins don't consume all suitable farm sites.
    jobs.sort(key=lambda r:r['size'][0]*r['size'][2],reverse=True)
    new=[]
    for item in jobs:
        sx,sy,sz=item['size'];placed=False
        for ci,(px,py) in enumerate(candidates):
            x0=px-sx//2;y0=py-sz//2;x1=x0+sx;y1=y0+sz
            box=(x0,y0,x1,y1);a,b,c,d=x0-26,y0-26,x1+27,y1+27
            if intersects(box,28):continue
            if not arbor[b:d,a:c].all() or watermask[b:d,a:c].any() or original_roads[b:d,a:c].any():continue
            patch=h[b:d,a:c].astype(float)/257
            if patch.min()<60 or np.ptp(patch)>8:continue
            level=round(float(h[py,px])/257)
            if level+item['yoffset']<6:continue
            occupied.append(box);candidates.pop(ci)
            r=dict(item,hub=1,service=False,center=[px-4096,4095-py],
                   height=level,position=[x0-4096,level,4095-y1],rotation=0,
                   footprint_image=list(box),hamlet=min(range(len(seeds)),key=lambda i:(px-seeds[i][0])**2+(py-seeds[i][1])**2))
            # 6 m flat apron, 20 m smooth transition. Leaves the original landform.
            yy,xx=np.mgrid[b:d,a:c]
            dist=np.maximum.reduce([x0-xx,xx-x1,y0-yy,yy-y1])
            w=np.clip((26-dist)/20,0,1);w=w*w*(3-2*w)
            h[b:d,a:c]=np.rint(h[b:d,a:c]*(1-w)+level*257*w).astype('<u2')
            # Gravel perimeter footpath provides access to doors on any facade.
            ring=(dist>=3)&(dist<=5)
            roads[b:d,a:c,1][ring]=255
            r['path_endpoint_image']=[px,y1+4]
            new.append(r);placed=True;break
        if not placed:raise RuntimeError(f'Only {len(new)} / {len(jobs)} fit, failed {item["source"]}')
    print('Placed',len(new),'new locations',flush=True)

    # One native-terrain walking network, connected to the pre-existing campaign road.
    # 8 m graph; forbid water, other biomes, ore seams and all POI interiors.
    step=8;size=1024
    safe=arbor.reshape(size,step,size,step).all(axis=(1,3))
    safe &= ~watermask.reshape(size,step,size,step).any(axis=(1,3))
    heights=h.reshape(size,step,size,step).mean(axis=(1,3))/257
    safe &= heights>=58
    for x0,y0,x1,y1 in occupied:
        safe[max(0,(y0-2)//step):min(size,(y1+2)//step+1),max(0,(x0-2)//step):min(size,(x1+2)//step+1)]=False
    # Endpoints are outside occupied footprints; connect them to the perimeter.
    for r in new:
        px,py=r['path_endpoint_image'];options=[]
        for gy in range(py//step,py//step+4):
            for gx in range(px//step-2,px//step+3):
                if safe[gy,gx]:options.append(((gx*step+4-px)**2+(gy*step+4-py)**2,gx,gy))
        if not options:raise RuntimeError('No safe path approach '+r['source'])
        _,gx,gy=min(options);r['path_node']=[gx,gy]
    source_nodes=original_roads.reshape(size,step,size,step).any(axis=(1,3)) & safe
    distances=np.full((size,size),np.inf);parent=np.full((size,size),-1,dtype=np.int32)
    heap=[]
    for gy,gx in zip(*np.where(source_nodes)):
        distances[gy,gx]=0;heap.append((0,int(gx),int(gy)))
    heapq.heapify(heap)
    targets={gy*size+gx for gx,gy in (r['path_node'] for r in new)}
    reached=set()
    while heap and len(reached)<len(targets):
        cost,x,y=heapq.heappop(heap)
        if cost!=distances[y,x]:continue
        node=y*size+x
        if node in targets:reached.add(node)
        for dx,dy in [(0,-1),(-1,0),(1,0),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
            nx,ny=x+dx,y+dy
            if not(0<=nx<size and 0<=ny<size) or not safe[ny,nx]:continue
            if dx and dy and (not safe[y,nx] or not safe[ny,x]):continue
            rise=abs(heights[ny,nx]-heights[y,x])
            if rise>2:continue
            nc=cost+step*math.hypot(dx,dy)+rise*12
            if nc<distances[ny,nx]:
                distances[ny,nx]=nc;parent[ny,nx]=node;heapq.heappush(heap,(nc,nx,ny))
    assert reached==targets, f'{len(targets-reached)} inaccessible sites'
    routes=[];edges=set()
    pathimage=Image.new('L',(8192,8192));draw=ImageDraw.Draw(pathimage)
    for r in new:
        gx,gy=r['path_node'];node=gy*size+gx;chain=[]
        while node>=0:
            x,y=node%size,node//size;chain.append((x*step+4,y*step+4))
            prev=int(parent[y,x])
            if prev>=0:edges.add(tuple(sorted((node,prev))))
            node=prev
        # Join the exact original road pixel, not merely its coarse graph cell.
        rx,ry=chain[-1];left=(rx//step)*step;top=(ry//step)*step
        ys,xs=np.where(original_roads[top:top+step,left:left+step])
        closest=min(zip(xs,ys),key=lambda v:(left+v[0]-rx)**2+(top+v[1]-ry)**2)
        chain.append((int(left+closest[0]),int(top+closest[1])))
        endpoint=tuple(r['path_endpoint_image']);draw.line([endpoint]+chain,fill=255,width=4)
        r['access']=[[x-4096,4095-y] for x,y in [endpoint]+chain]
        routes.append(chain)
    paths=np.asarray(pathimage)>0
    assert not np.any(paths & watermask),'Road crosses water'
    assert not np.any(paths & ~arbor),'Road leaves Arbor'
    roads[:,:,1][paths]=255
    # Publish the new world and all placement metadata only after graph success.
    OUT.mkdir(exist_ok=True,parents=True)
    for p in SOURCE.iterdir():
        if p.is_file() and p.name not in ['main.ttw','dtm.raw','splat3.png','locations-atlas.png','input-validation.json']:
            shutil.copy2(p,OUT/p.name)
    h[::-1].tofile(OUT/'dtm.raw');Image.fromarray(roads).save(OUT/'splat3.png')
    tree=E.parse(SOURCE/'prefabs.xml')
    bysource={r['source']:r for r in cat}
    for r in records:
        if r['hub']==1 and not r['service']:
            item=bysource[r['prefab']]
            node=next(p for p in tree.getroot() if p.get('name')==r['prefab'] and p.get('position')==','.join(map(str,r['position'])))
            node.set('name',item['prefab']);r.update(prefab=item['prefab'],quest_tags=item['quest_tags'])
    for r in new:E.SubElement(tree.getroot(),'decoration',type='model',name=r['prefab'],position=','.join(map(str,r['position'])),rotation='0',y_is_groundlevel='true')
    E.indent(tree);tree.write(OUT/'prefabs.xml',encoding='utf-8',xml_declaration=True)
    records+=new
    (OUT/'locations.json').write_text(json.dumps(records,indent=2))
    info=E.parse(SOURCE/'map_info.xml');info.find("property[@name='Name']").set('value','Allium-v0.8')
    info.find("property[@name='Description']").set('value','Allium: Wayrest and expanded Burnt Arbor exploration')
    info.write(OUT/'map_info.xml',encoding='utf-8',xml_declaration=True)
    # Separate authoring phase can be run before prefab conversion has finished.
    report={'world':'Allium-v0.8','arbor_total':sum(r['hub']==1 for r in records),
            'arbor_questable':sum(r['hub']==1 and questable(r['quest_tags'],r['tier']) for r in records),
            'new_placements':len(new),'gameplay_pois':len(records),'guaranteed_mineral_deposits':len(minerals),
            'tier_distribution':dict(collections.Counter(r['tier'] for r in records if r['hub']==1)),
            'used_variants':len({r['prefab'] for r in records if r['hub']==1 and not r['service']}),
            'hamlet_clusters':len({r['hamlet'] for r in new}),'path_graph_edges':len(edges),
            'new_block_definitions':0}
    (OUT/'arbor-build.json').write_text(json.dumps(report,indent=2))
    # Large world atlas for density and placement review.
    layout=json.loads((ROOT/'src/Worlds/Allium/layout.json').read_text())
    pixels=np.array(Image.open(SOURCE/'biomes.png').convert('RGB').resize((1536,1536),Image.Resampling.NEAREST));old=pixels.copy()
    for region in layout['regions']:pixels[np.all(old==region['game_rgb'],axis=2)]=region['preview_rgb']
    wet=np.asarray(Image.fromarray(watermask).resize((1536,1536),Image.Resampling.NEAREST))
    paths_preview=np.asarray(Image.fromarray(roads[:,:,1]).resize((1536,1536),Image.Resampling.NEAREST))
    pixels[wet]=(43,83,105);pixels[(paths_preview>0)&~wet]=(188,161,118)
    im=Image.fromarray(pixels);d=ImageDraw.Draw(im);scale=1536/8192
    for chain in routes:d.line([(x*scale,y*scale) for x,y in chain],fill='#bca176',width=1)
    for r in records:
        x,_,z=r['position'];sx,_,sz=r['size'];box=((x+4096)*scale,(4095-z-sz)*scale,(x+sx+4096)*scale,(4095-z)*scale)
        d.rectangle(box,fill='#f6ce66' if questable(r['quest_tags'],r['tier']) else '#29262c',outline='#e9dfca')
        if r['service']:d.text(((r['center'][0]+4096)*scale,(4095-r['center'][1])*scale),r['name'],fill='white',stroke_width=2,stroke_fill='black')
    d.rectangle((0,0,1536,42),fill='#17232b');d.text((12,12),'ALLIUM v0.8 / BURNT ARBOR: 480 LOCATIONS, 280 QUEST SITES / GOLD: QUESTABLE / DARK: EXPLORATION',fill='white')
    im.save(OUT/'locations-atlas.png')
    print(json.dumps(report,indent=2))

def publish_variants():
    cat=catalog();entries=list(E.parse(AUTHOR/'AlliumTools/arbor-art-report.xml').getroot())
    assert {e.get('source') for e in entries}=={r['source'] for r in cat}
    for r in cat:
        original=properties(NATIVE/(r['source']+'.xml'))
        path=AUTHOR/'DelveWayrest/Prefabs/POIs'/(r['prefab']+'.xml')
        changed=properties(path)
        for key,value in original.items():
            if key not in ['EditorGroups','ExcludeDistantPOIMesh','QuestTags']:assert changed[key]==value,(r['source'],key)
        assert changed.get('QuestTags','')==r['quest_tags']
        for ext in ['.xml','.tts','.blocks.nim']:
            p=path.with_name(r['prefab']+ext);assert p.stat().st_size>0;shutil.copy2(p,DEST/p.name)
    loc=ROOT/'src/DelveWayrest/Config/Localization.csv'
    with loc.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
    rows=[r for r in rows if not r[0].startswith('delve_arbor_')]
    rows += [[r['prefab'],'DelveWayrest','','','','',r['name']] for r in cat]
    with loc.open('w',encoding='utf-8',newline='') as f:csv.writer(f).writerows(rows)
    shutil.copy2(AUTHOR/'AlliumTools/arbor-art-report.xml',OUT/'arbor-art-report.xml')
    shutil.copy2(WORK/'catalog.json',OUT/'arbor-catalog.json')
    print('Published',len(entries),'serialized Arbor variants')

if __name__=='__main__':
    if '--catalog' in sys.argv:catalog()
    elif '--publish' in sys.argv:publish_variants()
    else:build()
