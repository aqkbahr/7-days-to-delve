"""Presentation-only vehicle/resin overlay; existing identifiers and gameplay survive."""
from pathlib import Path
import csv, json, re, shutil, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
GAME = Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config')
MOD = ROOT / 'src/ZZZDelveBatch01'
ART = ROOT / 'artifacts/batch-01/art'
for d in ['Config', 'Resources', 'UIAtlases/ItemIconAtlas']:
    (MOD/d).mkdir(parents=True, exist_ok=True)
(MOD/'ModInfo.xml').write_text('<xml><Name value="ZZZDelveBatch01"/><DisplayName value="Delve Batch 01"/><Version value="0.10.1"/><Author value="Delve"/><Description value="Wagon and crafting resin presentation; preserves native item and block identities."/></xml>\n')
blocks = {b.get('name'): b for b in ET.parse(GAME/'blocks.xml').getroot() if b.tag=='block'}
native_items = {b.get('name'): b for b in ET.parse(GAME/'items.xml').getroot() if b.tag=='item'}
def props(name):
    b=blocks[name]
    p={x.get('name'):x.get('value') for x in b.findall('property') if x.get('name')}
    return {**(props(p['Extends']) if p.get('Extends') in blocks else {}), **p}
patch = ET.Element('configs')
rows=[]
def replace(parent, kind, name, prop, value):
    path=f'/{kind}s/{kind}[@name="{name}"]'
    native=(blocks if kind=='block' else native_items)[name]
    if native.find(f'property[@name="{prop}"]') is not None:
        ET.SubElement(parent,'set',xpath=path+f'/property[@name="{prop}"]/@value').text=value
        return
    op=ET.SubElement(parent,'append',xpath=path)
    ET.SubElement(op,'property',name=prop,value=value)
for name,b in blocks.items():
    p=props(name); model=p.get('Model','')
    if 'Entities/Vehicles/' not in model or not name.startswith(('cnt','cars','carWrecks','burntSedan','abandoned','crushedCars')):
        continue
    stage=2 if any(x in model.lower() for x in ['dmg2','burntsedan','crushed_']) else 1 if any(x in model.lower() for x in ['dmg1','crumpled','abandonedvehicles']) else 0
    offset=p.get('ModelOffset','0,0,0').split(','); offset[1]='0'
    visual={'Model':f'#@modfolder:Resources/batchone.unity3d?delveWagon{stage}', 'ModelOffset':','.join(offset), 'CustomIcon':f'delveWagon{stage}', 'CustomIconTint':'FFFFFF', 'TintColor':'FFFFFF'}
    for key,value in visual.items(): replace(patch,'block',name,key,value)
    # Remove car fragments at each destruction stage. Regular material particles remain.
    if b.find('property[@name="ParticleOnDeath"]') is not None:
        ET.SubElement(patch,'remove',xpath=f'/blocks/block[@name="{name}"]/property[@name="ParticleOnDeath"]')
    # Generic native explosion visual (also used by explosives); damage/radii untouched.
    if b.findall('.//property[@name="ParticleIndex"]'):
        ET.SubElement(patch,'set',xpath=f'/blocks/block[@name="{name}"]//property[@name="ParticleIndex"]/@value').text='7'
    rows.append({'name':name,'stage':stage,'originalModel':model,'downgrade':p.get('DowngradeBlock',''),'offset':','.join(offset)})
ET.indent(patch); ET.ElementTree(patch).write(MOD/'Config/blocks.xml',encoding='utf-8',xml_declaration=True)
items=ET.Element('configs')
for key,value in {'CustomIcon':'delveCraftingResin','Meshfile':'#@modfolder:Resources/batchone.unity3d?delveCraftingResin','DropMeshfile':'#@modfolder:Resources/batchone.unity3d?delveCraftingResin'}.items():
    replace(items,'item','resourceScrapPolymers',key,value)
ET.indent(items); ET.ElementTree(items).write(MOD/'Config/items.xml',encoding='utf-8',xml_declaration=True)
loc={'resourceScrapPolymers':'Crafting Resin','resourceScrapPolymersDesc':'Hardened amber resin recovered from old bindings and salvaged goods. A versatile raw component used in crafting.'}
for row in rows: loc[row['name']]=['Cargo Wagon','Damaged Cargo Wagon','Stripped Wagon'][row['stage']]
with (GAME/'Localization.csv').open(encoding='utf-8-sig',newline='') as f:
    for row in csv.DictReader(f):
        text=row.get('english',''); key=row.get('Key','')
        if key in loc or not re.search(r'polymers|scrap polymer',text,re.I): continue
        loc[key]=re.sub(r'scrap polymers?|polymers', 'Crafting Resin',text,flags=re.I)
with (MOD/'Config/Localization.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english'])
    for key,text in loc.items():w.writerow([key,'DelveBatch01','',False,False,text])
shutil.copy2(ART/'Bundle/batchone.unity3d', MOD/'Resources/batchone.unity3d')
for stage in range(3):shutil.copy2(ART/f'Preview/wagon{stage}.png',MOD/f'UIAtlases/ItemIconAtlas/delveWagon{stage}.png')
shutil.copy2(ART/'Preview/delveCraftingResin.png',MOD/'UIAtlases/ItemIconAtlas/delveCraftingResin.png')
(ROOT/'artifacts/batch-01/vehicles.json').write_text(json.dumps(rows,indent=2))
# A precise mechanical-scope assertion: only these presentation operations are permitted.
allowed={'Model','ModelOffset','CustomIcon','CustomIconTint','TintColor','ParticleOnDeath','ParticleIndex'}
for op in patch:
    property_name=re.findall(r'property\[@name="([^"]+)"\]',op.get('xpath',''))
    if op.tag=='append':property_name=[x.get('name') for x in op]
    assert set(property_name)<=allowed and property_name
assert len(rows)>100 and {r['stage'] for r in rows}=={0,1,2}
assert all(not r['downgrade'] or r['downgrade'] in {x['name'] for x in rows} for r in rows)
checks=ET.Element('vehicles')
for row in rows:ET.SubElement(checks,'vehicle', {k:str(v) for k,v in row.items()})
ET.ElementTree(checks).write(ROOT/'artifacts/batch-01/vehicles.xml',encoding='utf-8',xml_declaration=True)
print(f'PASS: {len(rows)} static road vehicle variants, all linked stages; {len(loc)} localization overrides; presentation-only scope.')
