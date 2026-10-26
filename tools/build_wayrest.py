"""Author Wayrest's voxel blueprint and standalone XML content module."""
from pathlib import Path
import csv, copy, json, sys, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
mod=ROOT/'src/DelveWayrest';config=mod/'Config';config.mkdir(parents=True,exist_ok=True)
out=ROOT/'artifacts/wayrest';out.mkdir(parents=True,exist_ok=True)
native=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config')
def save(path,root):
    ET.indent(root);ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
def patch(file,target,entries):
    root=ET.Element('configs');append=ET.SubElement(root,'append',xpath=target)
    append.extend(entries);save(config/file,root)
if '--geometry-only' not in sys.argv:
    save(mod/'ModInfo.xml',ET.fromstring('<xml><Name value="DelveWayrest"/><DisplayName value="Delve - Wayrest"/><Version value="0.1.0"/><Description value="Custom Wayrest settlement and steward"/><Author value="Delve"/></xml>'))
    patch('blocks.xml','/blocks',[ET.fromstring('<block name="delveWayrestStewardSpawn"><property name="Extends" value="spawnTrader"/><property name="SpawnClass" value="delveWayrestSteward"/></block>')])
    patch('entityclasses.xml','/entity_classes',[ET.fromstring('<entity_class name="delveWayrestSteward" extends="npcTraderJoel"><property name="NPCID" value="delveWayrestSteward"/><property name="UserSpawnType" value="None"/></entity_class>')])
    npc=copy.deepcopy(ET.parse(native/'npc.xml').getroot().find("npc_info[@id='traitorjoel']"))
    npc.attrib.update(id='delveWayrestSteward',name='Wayrest Steward',name_key='delveWayrestSteward',localization_id='delveWayrestSteward',dialog_id='delveWayrest')
    patch('npc.xml','/npc',[npc])
    dialog=copy.deepcopy(ET.parse(native/'dialogs.xml').getroot().find("dialog[@id='trader']"));dialog.set('id','delveWayrest')
    start=dialog.find("statement[@id='start']");start.set('text','delveWayrestGreeting')
    start.insert(0,ET.Element('response_entry',id='wayrestWelcome'))
    ET.SubElement(dialog,'response',id='wayrestWelcome',text='delveWayrestAskWelcome',nextstatementid='wayrestWelcome')
    s=ET.SubElement(dialog,'statement',id='wayrestWelcome',text='delveWayrestWelcome')
    ET.SubElement(s,'quest_entry',id='delveWayrestSupplies',type='add',listindex='0')
    ET.SubElement(s,'response_entry',id='nevermind')
    # The separate Delve tutorial replaces vanilla IntroComplete; allow native jobs.
    for response in dialog.findall('response'):
        for requirement in list(response):
            if requirement.tag=='requirement' and requirement.get('id')=='IntroComplete':response.remove(requirement)
    patch('dialogs.xml','/dialogs',[dialog])
    quest=ET.Element('quest',id='delveWayrestSupplies')
    for k,v in {'name_key':'delveWayrestSupplies','subtitle_key':'delveWayrestSuppliesSub','description_key':'delveWayrestSuppliesDesc','offer_key':'delveWayrestSuppliesDesc','icon':'ui_game_symbol_campfire','category_key':'delveQuestCategory','repeatable':'false','shareable':'false','add_to_tier_complete':'false','completiontype':'AutoComplete'}.items():ET.SubElement(quest,'property',name=k,value=v)
    ET.SubElement(quest,'objective',type='FetchKeep',id='resourceWood',value='30',phase='1')
    ET.SubElement(quest,'objective',type='FetchKeep',id='resourceRockSmall',value='20',phase='1')
    ET.SubElement(quest,'objective',type='Craft',id='delveHealingPoultice',value='2',phase='2')
    ET.SubElement(quest,'reward',type='Exp',value='250');ET.SubElement(quest,'reward',type='Item',id='casinoCoin',value='50')
    patch('quests.xml','/quests',[quest])
    strings={'delve_wayrest_01':'Wayrest','delveWayrestSteward':'Wayrest Steward','delveWayrestGreeting':'Welcome to Wayrest. Supplies and work are handled here in the hall.',
    'delveWayrestAskWelcome':'Tell me about Wayrest.',
    'delveWayrestWelcome':'The hearth marks our meeting place. The smithy stands west of it, the storehouse east. Take what you learn here into the frontier. Ask me for supplies or work. Our next road leads to Arbor Camp. This first supply exercise is personal preparation; it does not advance reclamation.',
    'delveWayrestSupplies':'Wayrest: Ready for the Frontier','delveWayrestSuppliesSub':'Gather supplies and prepare healing poultices.',
    'delveWayrestSuppliesDesc':'Gather 30 wood and 20 small stones, then craft two healing poultices. You keep your supplies. This one-time preparation task is separate from settlement reclamation.'}
    with (config/'Localization.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','KeepLoaded','english'])
        for k,v in strings.items():writer.writerow([k,'DelveWayrest','','','','',v])

vox=np.full((60,18,60),'air',dtype=object)
rot=np.zeros(vox.shape,dtype=np.uint8)
damage=np.zeros(vox.shape,dtype=np.uint16)
def fill(x1,y1,z1,x2,y2,z2,name):vox[x1:x2+1,y1:y2+1,z1:z2+1]=name
stone='cobblestoneShapes:cube';wood='woodShapes:cube';log='woodLogPillar100'
fill(0,0,0,59,1,59,'terrDirt')
fill(27,1,3,32,1,44,stone);fill(7,1,23,53,1,31,stone)
# Perimeter with generous open southern gate. No fabricated closing gate system.
for x in range(3,57):
    for z in [3,56]:
        if 26<=x<=33:continue
        fill(x,2,z,x,4+(x%2),z,log)
for z in range(4,56):
    for x in [3,56]:fill(x,2,z,x,4+(z%2),z,log)
buildings=[('Steward hall',(21,39,40,53)),('Smithy',(7,29,18,41)),('Storehouse',(43,29,53,41)),('Rest shelter',(7,9,20,20)),('Wayside shrine',(43,10,53,21))]
for name,(x1,z1,x2,z2) in buildings:
    fill(x1,1,z1,x2,1,z2,stone)
    for y in range(2,7):
        material=stone if y==2 else wood
        fill(x1,y,z1,x2,y,z1,material);fill(x1,y,z2,x2,y,z2,material)
        fill(x1,y,z1,x1,y,z2,material);fill(x2,y,z1,x2,y,z2,material)
    mid=(x1+x2)//2
    # South-facing, three-block-wide open door; windows on east and west.
    fill(mid-1,2,z1,mid+1,4,z1,'air')
    fill(x1,4,z1+4,x1,5,z1+6,'air');fill(x2,4,z1+4,x2,5,z1+6,'air')
    for x in [x1,x2]:
        for z in [z1,z2]:fill(x,2,z,x,6,z,log)
    # Native ramp blocks form actual slanted roof planes, with overhanging eaves.
    ridge=(z1+z2)//2
    for z in range(z1-1,z2+2):
        h=7+max(0,min(z-z1,z2-z))
        for x in range(x1-1,x2+2):
            vox[x,h,z]='woodShapes:ramp';rot[x,h,z]=2 if z<=ridge else 0
        if z1<=z<=z2:
            fill(x1,7,z,x1,h-1,z,wood);fill(x2,7,z,x2,h-1,z,wood)
    # Inset half-block window sills, timber mullions and patched masonry.
    for x in (x1,x2):
        for z in range(z1+4,z1+7):vox[x,3,z]='woodShapes:cubeHalf'
        fill(x,4,z1+5,x,5,z1+5,log)
    # Porch with a lean-to roof and pillars framing the open entrance.
    for x in (mid-2,mid+2):fill(x,2,z1-3,x,5,z1-3,log)
    for z in range(z1-3,z1):
        fill(mid-2,5+(z-(z1-3)),z,mid+2,5+(z-(z1-3)),z,'woodShapes:ramp')
        rot[mid-2:mid+3,5+(z-(z1-3)),z]=2
    # Stone chimney supported from the foundation, outside each service area.
    if name in ('Smithy','Steward hall'):
        fill(x2-2,2,z2-2,x2-2,11,z2-2,stone)
        vox[x2-2,12,z2-2]='cobblestoneShapes:cubeHalf'
    # Authored cosmetic wear leaves supporting walls intact.
    for x in range(x1+2,x2-1,4):damage[x,2,z1]=35
    # Interior roof beam prevents long unsupported spans.
    fill(mid,6,z1,mid,6,z2,log)
    fill(mid,2,z2-1,mid,6,z2-1,log)
    fill(mid-1,1,z1-5,mid+1,1,z1-1,stone)
# Hall desk, single steward; no duplicate service NPCs.
fill(26,2,47,34,2,47,wood)
fill(30,2,49,30,2,49,'delveWayrestStewardSpawn')
fill(26,3,47,26,3,47,'candleTableLight')
fill(9,2,38,9,2,38,'forge');fill(14,2,38,14,2,38,'workbench')
for x in [45,49]:fill(x,2,38,x,2,38,'cntWoodenChestClosed')
for x in [9,13,17]:fill(x,2,17,x,2,17,'bedroll')
fill(46,2,18,50,2,18,stone);fill(48,3,18,48,3,18,'candleTableLight')
# Open gathering square and four short benches around the hearth.
fill(24,1,22,36,1,33,stone);fill(30,2,27,30,2,27,'campfire')
for z in [23,31]:fill(26,2,z,28,2,z,wood);fill(32,2,z,34,2,z,wood)
for x in [25,34]:fill(x,2,4,x,6,4,log);fill(x,7,4,x,7,4,'candleTableLight')
# Rear gate has a continuous approach around the hall, without moving its services.
fill(27,1,54,32,1,59,stone)
fill(19,1,32,20,1,55,stone);fill(19,1,54,32,1,55,stone)
for x in (25,34):
    fill(x,2,56,x,6,56,log)
    fill(x,7,56,x,7,56,'candleTableLight')
# Prove a two-block-high walking route from the gate to each open doorway/NPC.
walk=(vox[:,2,:]=='air')&(vox[:,3,:]=='air')
start=(30,5);seen={start};todo=[start]
while todo:
    x,z=todo.pop()
    for nx,nz in [(x-1,z),(x+1,z),(x,z-1),(x,z+1)]:
        if 0<=nx<60 and 0<=nz<60 and walk[nx,nz] and (nx,nz) not in seen:seen.add((nx,nz));todo.append((nx,nz))
for name,(x1,z1,x2,z2) in buildings:assert ((x1+x2)//2,z1+1) in seen,name+' inaccessible'
assert (29,49) in seen,'Steward not reachable'
assert (30,58) in seen,'Rear gate not reachable'
assert np.count_nonzero(vox=='delveWayrestStewardSpawn')==1
root=ET.Element('blueprint',size='60,18,60')
# Run-length encode rows; the runtime resolves native IDs and writes .tts/.nim.
for y in range(18):
    for z in range(60):
        x=0
        while x<60:
            name=vox[x,y,z];end=x
            while end+1<60 and vox[end+1,y,z]==name and rot[end+1,y,z]==rot[x,y,z] and damage[end+1,y,z]==damage[x,y,z]:end+=1
            if name!='air':ET.SubElement(root,'row',x=str(x),y=str(y),z=str(z),end=str(end),block=name,rotation=str(rot[x,y,z]),damage=str(damage[x,y,z]))
            x=end+1
save(out/'blueprint.xml',root)
(out/'design.json').write_text(json.dumps({'size':[60,18,60],'origin_world':[-2711,63,-2182],'buildings':buildings,'steward_local':[30,2,49],'solid_blocks':int(np.count_nonzero(vox!='air')),'walk_checks':'PASS: all five doorways and steward approach reachable from gate in voxel plan'},indent=2))
# Blueprint plan, generated directly from the authored voxel geometry.
im=Image.new('RGB',(1000,1080),'#17252c');draw=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
palette={stone:'#a2a091',wood:'#a47847',log:'#6c462b','terrDirt':'#63724b','air':'#63724b'}
for x in range(60):
    for z in range(60):
        # Show walls/furnishings with roofs removed.
        col=vox[x,:7,z];idx=np.where(col!='air')[0];name=col[idx[-1]] if len(idx) else 'air'
        color=palette.get(name,'#d9b66f');px=50+x*15;py=85+(59-z)*15
        draw.rectangle((px,py,px+14,py+14),fill=color)
draw.text((50,25),'WAYREST / CUSTOM SETTLEMENT / NORTH UP / ROOFS REMOVED',font=font,fill='white')
for name,(x1,z1,x2,z2) in buildings:
    px=50+x1*15;py=85+(59-z2)*15+15
    draw.text((px+3,py),name,font=small,fill='white',stroke_width=2,stroke_fill='#17252c')
draw.text((440,550),'HEARTH',font=font,fill='white',stroke_width=2,stroke_fill='#17252c')
draw.text((445,944),'GATE',font=font,fill='white',stroke_width=2,stroke_fill='#17252c')
draw.text((50,1005),'One steward | native trade/jobs | timber + stone | open access',font=font,fill='white')
draw.text((50,1040),'Voxel connectivity checked. Visual playtesting remains deferred.',font=small,fill='#b8c7cf')
im.save(out/'wayrest-plan.png');print(out)
if '--geometry-only' not in sys.argv:
    import runpy
    runpy.run_path(str(ROOT/'tools/build_wayrest_campaign.py'))

    # Apply shared first-playthrough story after generation.
    from intro_story import apply_wayrest
    apply_wayrest()
