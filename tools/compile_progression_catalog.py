"""Compile reviewed draft layouts into a stable registry. Effects are explicit,
never inferred from prose. Unsupported entries stay locked and cannot cost points.
"""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
specs=[
 ('Blades','progression-melee-magic-draft.txt','BLADES —','Suggested Trial of the Blade'),
 ('Blunt','progression-melee-magic-draft.txt','BLUNT —','Suggested Trial of the Hammer'),
 ('Polearms','progression-polearms-unarmed-draft.txt','POLEARMS —','Trial of the Reach: authored'),
 ('Unarmed','progression-polearms-unarmed-draft.txt','UNARMED —','Trial of the Open Hand: an'),
 ('Archery','progression-archery-draft.txt','10 — SHARED FUNDAMENTALS','AMMUNITION AND CRAFTING BOUNDARIES'),
]
for skill,head in [('Wands','WANDS'),('Staffs','STAFFS'),('Totems','TOTEMS')]: specs.append((skill,'progression-magic-draft.txt',head+' —','Trial proposal:'))
for skill,head in [('HeavyArmor','HEAVY ARMOR'),('MediumArmor','MEDIUM ARMOR'),('LightArmor','LIGHT ARMOR')]: specs.append((skill,'progression-armor-draft.txt',head+' —','Trial proposal:'))
for skill,head in [('PackMule','PACK MULE'),('Stealth','STEALTH'),('Athletics','ATHLETICS')]: specs.append((skill,'progression-movement-draft.txt',head+' —','Trial proposal:'))
for skill in ['Farming','Cooking','Mining','Smithing','Carpentry','Alchemy']: specs.append((skill,'progression-crafting-draft.txt',skill.upper()+' —','Trial:'))
def ident(s): return re.sub('[^A-Za-z0-9]','',s)
trees=[]
for skill,file,start,end in specs:
 source=(ROOT/'docs'/file).read_text(encoding='utf-8-sig')
 text=re.split('^'+re.escape(start),source,maxsplit=1,flags=re.M)[1].split(end,1)[0]
 if skill!='Archery':
  text=re.split(r'(?:10 — Fundamentals \(2\)|Fundamentals(?:, proficiency 10| at 10):)',text,maxsplit=1)[1]
 ordinary=[];caps=[];current=None;cap=False
 for line in text.splitlines():
  if re.match(r'(100 —|Choose ONE mastery|Choose ONE mastery at)',line): cap=True;current=None;continue
  m=re.match(r'^\s*(?:(20|40|60|80) )?([A-Z][A-Za-z0-9\x27’ /-]+?)(?: \(also requires [^)]*\))?: (.*)$',line)
  if m and (cap or m[1] or len(ordinary)<2):
   rank=100 if cap else int(m[1] or 10)
   current={'id':'delvePerk'+skill+ident(m[2]),'name':m[2],'rank':rank,'description':m[3],'implemented':False,'effects':[]}
   (caps if cap else ordinary).append(current)
  elif current and line.startswith('  '): current['description']+=' '+line.strip()
  elif line and not line.startswith(' '): current=None
 assert len(ordinary)==14,(skill,len(ordinary),[x['name'] for x in ordinary])
 assert len(caps)==({'Blades':6,'Blunt':5}.get(skill,4)),(skill,len(caps))
 for i,p in enumerate(ordinary):
  p['prerequisites']=[] if i<2 else [x['id'] for x in ordinary[:2]] if p['rank']==20 else [ordinary[i-1]['id']]
 for p in caps: p['prerequisites']=[x['id'] for x in ordinary]
 trees.append({'skill':skill,'source':file,'perks':ordinary+caps})
(ROOT/'src/Progression').mkdir(exist_ok=True)
(ROOT/'src/Progression/trees.json').write_text(json.dumps(trees,indent=2,ensure_ascii=False),encoding='utf-8')
print('Registered',len(trees),'trees,',sum(len(t['perks']) for t in trees),'perk choices')
