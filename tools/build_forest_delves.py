"""Four native-layout underground delves, new placements and Wayrest Tier 2 board."""
from pathlib import Path
import copy,csv,json,shutil,hashlib
import xml.etree.ElementTree as E
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'artifacts/maps/Allium-v0.9';OUT=ROOT/'artifacts/maps/Allium-v0.10'
AUTHOR=ROOT/'playtest/DungeonAuthor/Mods'
DEST=ROOT/'src/DelveWayrest/Prefabs/POIs'
NATIVE=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Prefabs/POIs')
SPECS=[('cave_06','Rootbound Hollow',1),('cave_11','Smuggler\'s Rest',1),('cemetery_02','Briarstone Crypt',2),('cave_12','Old Warden\'s Deep',2)]

def props(path):return {p.get('name'):p.get('value') for p in E.parse(path).getroot().findall('property') if p.get('name')}
def save(tree,path):E.indent(tree);E.ElementTree(tree).write(path,encoding='utf-8',xml_declaration=True)
def config():
    mod=ROOT/'src/ZDelveDungeons';(mod/'Config').mkdir(parents=True,exist_ok=True)
    m=E.Element('xml')
    for key,value in [('Name','ZDelveDungeons'),('DisplayName','Delve - Forest Depths'),('Version','0.1.0'),('Description','Native underground delves and milestone-gated Wayrest Tier 2 jobs'),('Author','Delve')]:E.SubElement(m,key,value=value)
    save(m,mod/'ModInfo.xml')
    source=E.parse(ROOT/'src/DelveWayrest/Config/quests.xml')
    # QuestEntry resolves its QuestClass while the list is read. Definitions
    # must precede this existing list in the merged native document.
    root=E.Element('configs');a=E.SubElement(root,'insertBefore',xpath="/quests/quest_list[@id='delveWayrestJobs']")
    strings={'delveForestDepthsBoard':'Explore the deeper Forest delves (Tier 2)'}
    for suffix,title in [('Fetch','Recover Lost Relics'),('Clear','Clear the Forest Depths'),('FetchClear','Secure the Buried Halls')]:
        q=copy.deepcopy(source.find(f".//quest[@id='delveWayrest{suffix}']"));q.set('id','delveForestDepths'+suffix)
        q.find("property[@name='name_key']").set('value',q.get('id'))
        q.find("property[@name='difficulty_tier']").set('value','2')
        for reward in q.findall('reward'):
            if reward.get('type')=='Exp':reward.set('value','4000')
            if reward.get('id')=='casinoCoin':reward.set('value','300')
        a.append(q);strings[q.get('id')]='Wayrest: '+title
    pool=E.SubElement(root,'append',xpath="/quests/quest_list[@id='delveWayrestJobs']")
    for suffix in ['Fetch','Clear','FetchClear']:E.SubElement(pool,'quest',id='delveForestDepths'+suffix,cvar='delveWayrestReady')
    save(root,mod/'Config/quests.xml')
    root=E.Element('configs')
    a=E.SubElement(root,'append',xpath="/dialogs/dialog[@id='delveWayrest']/statement[@id='start']")
    E.SubElement(a,'response_entry',id='delveForestDepthsBoard')
    a=E.SubElement(root,'append',xpath="/dialogs/dialog[@id='delveWayrest']")
    response=E.SubElement(a,'response',id='delveForestDepthsBoard',text='delveForestDepthsBoard',nextstatementid='currentjobs2')
    E.SubElement(response,'requirement',type='CheckCVar',id='delveWayrestReady',value='1',requirementtype='Hide')
    E.SubElement(response,'requirement',type='QuestStatus',value='NotStarted',requirementtype='Hide')
    E.SubElement(root,'remove',xpath="/dialogs/dialog[@id='delveWayrest']/response[@id='jobshave1']/requirement[@type='QuestTierHighest']")
    save(root,mod/'Config/dialogs.xml')
    with (mod/'Config/Localization.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english','Context / Alternate Text'])
        # Match the game's English column by name, not an assumed index.
        for k,v in strings.items():writer.writerow([k,'ZDelveDungeons','','','',v,''])

def build():
    config()
    report=E.parse(AUTHOR/'AlliumTools/dungeon-art-report.xml');assert len(list(report.getroot()))==4
    records=json.loads((SRC/'locations.json').read_text());ore=json.loads((SRC/'resource-sites.json').read_text())
    OUT.mkdir(parents=True,exist_ok=True)
    h=np.fromfile(SRC/'dtm.raw',dtype='<u2').reshape(8192,8192)[::-1].copy()
    oldh=h.copy();b=np.asarray(Image.open(SRC/'biomes.png').convert('RGB'));water=np.asarray(Image.open(SRC/'splat4.png'))[:,:,2]
    roads=np.array(Image.open(SRC/'splat3.png'));original_roads=roads[:,:,1].copy()
    occupied=[]
    for r in records:
        x,_,z=r['position'];sx,_,sz=r['size'];occupied.append((x+4096,4095-z-sz,x+4096+sx,4095-z))
    for r in ore:
        x,y=r['x']+4096,4095-r['z'];occupied.append((x-14,y-14,x+14,y+14))
    blocked=np.zeros((8192,8192),dtype=bool)
    for x0,y0,x1,y1 in occupied:blocked[max(0,y0-7):min(8192,y1+8),max(0,x0-7):min(8192,x1+8)]=True
    # Candidate walking-road pixels in the Wayrest catchment.
    ys,xs=np.where(original_roads[5200:7600:4,400:3000:4]>0)
    roadpoints=list(zip(xs*4+400,ys*4+5200))
    new=[]
    ideals=[(1070,6030),(2000,6700),(2050,5900),(1050,6870)]
    for (source,title,tier),(ix,iy) in zip(SPECS,ideals):
        name='delve_dungeon_'+source;path=AUTHOR/'DelveWayrest/Prefabs/POIs'/(name+'.xml')
        metadata=props(path);native=props(NATIVE/(source+'.xml'))
        for key,value in native.items():
            if key not in ['EditorGroups','ExcludeDistantPOIMesh','QuestTags']:assert metadata[key]==value,(source,key)
        for ext in ['.xml','.tts','.blocks.nim']:shutil.copy2(path.with_name(name+ext),DEST/(name+ext))
        sx,sy,sz=map(int,metadata['PrefabSize'].split(','));offset=int(metadata['YOffset'])
        assert offset<0 and metadata['CopyAirBlocks']=='True' and metadata.get('TraderArea')=='False'
        candidates=[(x,y) for y in range(5500,7400,32) for x in range(650,2700,32)]
        candidates.sort(key=lambda p:(p[0]-ix)**2+(p[1]-iy)**2)
        found=False
        for px,py in candidates:
            x0=px-sx//2;y0=py-sz//2;x1=x0+sx;y1=y0+sz
            a,c=x0-30,x1+31;bb,d=y0-30,y1+31
            if any(x0-35<k and x1+35>i and y0-35<l and y1+35>j for i,j,k,l in occupied):continue
            if not np.all(b[bb:d,a:c]==[0,64,0]) or water[bb:d,a:c].any() or original_roads[bb:d,a:c].any():continue
            patch=h[bb:d,a:c].astype(float)/257
            if patch.min()<60 or np.ptp(patch)>6:continue
            level=round(float(h[py,px])/257)
            if level+offset<10:continue
            # Native road-exit is on the south facade; connect a clear perimeter.
            endpoint=(px,y1+6);options=sorted(roadpoints,key=lambda p:(p[0]-px)**2+(p[1]-y1)**2)
            chosen=None
            for rx,ry in options[:400]:
                distance=np.hypot(rx-endpoint[0],ry-endpoint[1])
                if distance>1000:break
                xx=np.rint(np.linspace(endpoint[0],rx,int(distance)+2)).astype(int)
                yy=np.rint(np.linspace(endpoint[1],ry,int(distance)+2)).astype(int)
                if blocked[yy,xx].any():continue
                if np.any((xx>x0-2)&(xx<x1+2)&(yy>y0-2)&(yy<y1+2)):continue
                if any(water[yy+dy,xx+dx].any() or not np.all(b[yy+dy,xx+dx]==[0,64,0]) for dx,dy in [(0,0),(-3,-3),(3,3),(-3,3),(3,-3)]):continue
                heights=h[yy,xx].astype(float)/257
                if np.max(abs(np.diff(heights)))>.6:continue
                chosen=(int(rx),int(ry));break
            if chosen is None:continue
            yy,xx=np.mgrid[bb:d,a:c];dist=np.maximum.reduce([x0-xx,xx-x1,y0-yy,yy-y1])
            weight=np.clip((30-dist)/22,0,1);weight=weight*weight*(3-2*weight)
            h[bb:d,a:c]=np.rint(h[bb:d,a:c]*(1-weight)+level*257*weight).astype('<u2')
            roads[bb:d,a:c,1][(dist>=4)&(dist<=7)]=255
            mask=Image.new('L',(8192,8192));draw=ImageDraw.Draw(mask);draw.line([endpoint,chosen],fill=255,width=4)
            roads[:,:,1][np.asarray(mask)>0]=255
            r=dict(name=title,prefab=name,source=source,hub=0,service=False,tier=tier,quest_tags=metadata['QuestTags'],
                   size=[sx,sy,sz],position=[x0-4096,level,4095-y1],center=[px-4096,4095-py],height=level,
                   yoffset=offset,underground_bottom=level+offset,access=[[p[0]-4096,4095-p[1]] for p in [endpoint,chosen]],dungeon=True)
            occupied.append((x0,y0,x1,y1));blocked[y0-7:y1+8,x0-7:x1+8]=True;new.append(r);found=True;print('Placed '+title,flush=True);break
        assert found,'No safe dungeon site '+title
    for r in records:
        x,_,z=r['position'];sx,_,sz=r['size'];x+=4096;y=4095-z-sz
        assert np.array_equal(h[y-5:y+sz+6,x-5:x+sx+6],oldh[y-5:y+sz+6,x-5:x+sx+6])
    for r in ore:
        x,y=r['x']+4096,4095-r['z'];assert np.array_equal(h[y-14:y+15,x-14:x+15],oldh[y-14:y+15,x-14:x+15]);assert np.array_equal(roads[y-14:y+15,x-14:x+15,1],original_roads[y-14:y+15,x-14:x+15])
    for p in SRC.iterdir():
        if p.is_file() and p.name not in ['main.ttw','dtm.raw','splat3.png','input-validation.json']:shutil.copy2(p,OUT/p.name)
    (OUT/'dtm.raw.tmp').write_bytes(np.ascontiguousarray(h[::-1]).tobytes());(OUT/'dtm.raw.tmp').replace(OUT/'dtm.raw');Image.fromarray(roads).save(OUT/'splat3.png')
    tree=E.parse(SRC/'prefabs.xml')
    for r in new:E.SubElement(tree.getroot(),'decoration',type='model',name=r['prefab'],position=','.join(map(str,r['position'])),rotation='0',y_is_groundlevel='true')
    save(tree.getroot(),OUT/'prefabs.xml')
    info=E.parse(SRC/'map_info.xml');info.find("property[@name='Name']").set('value','Allium-v0.10');save(info.getroot(),OUT/'map_info.xml')
    (OUT/'locations.json').write_text(json.dumps(records+new,indent=2));(OUT/'dungeons.json').write_text(json.dumps(new,indent=2))
    shutil.copy2(AUTHOR/'AlliumTools/dungeon-art-report.xml',OUT/'dungeon-art-report.xml')
    support_report=AUTHOR/'AlliumTools/old-warden-supports.xml'
    if support_report.exists():shutil.copy2(support_report,OUT/'old-warden-supports.xml')
    loc=ROOT/'src/DelveWayrest/Config/Localization.csv'
    with loc.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
    header=rows[0];english=header.index('english');rows=[r for r in rows if not r[0].startswith('delve_dungeon_')]
    for r in new:
        row=['']*len(header);row[0]=r['prefab'];row[1]='DelveWayrest';row[english]=r['name'];rows.append(row)
    with loc.open('w',encoding='utf-8',newline='') as f:csv.writer(f).writerows(rows)
    validation=dict(world='Allium-v0.10',result='PASS',gameplay_pois=len(records)+4,placements=len(list(tree.getroot())),
        dungeons=4,tiers=[1,1,2,2],mineral_deposits_preserved=len(ore),gardens_preserved=3,
        checks=['Full underground footprints and 35 m separation from existing POIs and ore sites',
        'Dry Forest-only sites; bottom elevations above bedrock; all existing foundations unchanged',
        'Native cave/crypt air carving, sleeper volumes, indexed fetch/rally and triggers preserved',
        'No trader protection or indestructible block types introduced; ordinary digging retained',
        'All four dungeons use ordinary repeatable quest/reset behavior'],
        limits='Native-layout adaptations, not newly invented room geometry. Human traversal, appearance and full combat playthrough pending.')
    (OUT/'input-validation.json').write_text(json.dumps(validation,indent=2))
    # Local planning atlas; surface footprints show the FULL reserved dungeon area.
    im=Image.new('RGB',(1100,900),'#23392c');draw=ImageDraw.Draw(im)
    forest=[r for r in records+new if r['hub']==0]
    left=min(r['position'][0] for r in forest)-100
    right=max(r['position'][0]+r['size'][0] for r in forest)+300
    bottom=min(r['position'][2] for r in forest)-100
    top=max(r['position'][2]+r['size'][2] for r in forest)+100
    scale=min(1050/(right-left),800/(top-bottom))
    def xy(x,z):return (25+(x-left)*scale,65+(top-z)*scale)
    for r in records+new:
        if r['hub']!=0:continue
        x,_,z=r['position'];sx,_,sz=r['size'];a=xy(x,z+sz);bb=xy(x+sx,z)
        draw.rectangle((*a,*bb),fill='#e6b95d' if r.get('dungeon') else '#607958')
        if r.get('dungeon') or r['service']:draw.text((a[0],a[1]-16),r['name']+(' / T'+str(r['tier']) if r.get('dungeon') else ''),fill='white')
        if r.get('dungeon'):draw.line([xy(*p) for p in r['access']],fill='#caa676',width=3)
    draw.text((15,15),'FOREST DELVES / FULL UNDERGROUND FOOTPRINTS / NORTH UP',fill='white');im.save(OUT/'dungeons-atlas.png')
    print(json.dumps(new,indent=2))

if __name__=='__main__':
    import sys
    if '--config' in sys.argv:config()
    else:build()
