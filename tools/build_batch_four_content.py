"""Presentation/recipe/loot overlays; preserve container mechanics and POI planting."""
from pathlib import Path
from lxml import etree as E
import csv,json,copy
import build_forest_slice as merger
R=Path(__file__).resolve().parents[1]
M=R/'src/ZZZZZZZDelveBatch04'; C=M/'Config';C.mkdir(parents=True,exist_ok=True)
merger.MOD_NAMES=sorted(p.name for p in (R/'src').iterdir() if (p/'ModInfo.xml').exists() and p!=M)
docs={k:merger.merge(R/'src',k) for k in ('blocks','recipes','loot','biomes')}
def save(name,root): E.indent(root);E.ElementTree(root).write(str(C/(name+'.xml')),encoding='utf-8',xml_declaration=True)
(M/'ModInfo.xml').write_text('<xml><Name value="ZZZZZZZDelveBatch04"/><DisplayName value="Delve Playtest Batch 4"/><Version value="0.10.6"/><Author value="Delve"/></xml>')
loot=E.Element('configs');E.SubElement(loot,'set',xpath="/lootcontainers//item[@name='oldCash']/@name").text='resourcePaper';save('loot',loot)
recipes=E.Element('configs');changes=[]
plants={'resourceCropChrysanthemumPlant','resourceCropGoldenrodPlant','resourceDelveMooncap','delveMooncap','delveHerbalExtract','delveYarrow','delveThyme','delveMarigold','delveSage','delveLavender'}
for recipe in docs['recipes'].getroot():
 n=recipe.get('name') or ''
 if not ('Rune' in n and ('Wand' in n or 'Staff' in n)):continue
 for ingredient in recipe.findall('ingredient'):
  old=ingredient.get('name')
  if old not in plants:continue
  new='resourceScrapLead' if 'Wand' in n else 'resourceScrapIron'
  xp=f"/recipes/recipe[@name='{n}']/ingredient[@name='{old}']/@name"
  if xp not in [e.get('xpath') for e in recipes]:E.SubElement(recipes,'set',xpath=xp).text=new
  changes.append([n,old,new])
save('recipes',recipes)
blocks=E.Element('configs');names=[]
for b in docs['blocks'].getroot():
 n=b.get('name') or '';model=None
 if n.startswith('planted'):
  if b.find("property[@name='DisplayInfo']") is not None:E.SubElement(blocks,'remove',xpath=f"/blocks/block[@name='{n}']/property[@name='DisplayInfo']")
  a=E.SubElement(blocks,'append',xpath=f"/blocks/block[@name='{n}']");E.SubElement(a,'property',name='DisplayInfo',value='None')
 if n.startswith(('cntMedicLootPile','cntMedicineCabinet','cntPill')):model='delveApothecaryChest'
 elif n.startswith(('cntShippingCrate','cntLootCrate','cntLootChestHero','cntHardenedChest','cntBuried','cntTestTreasureChest')):model='delveIronboundChest'
 if model:
  names.append([n,model])
  for k,v in {'Model':f'#@modfolder:Resources/batchfour.unity3d?{model}','CustomIcon':model,'TintColor':'FFFFFF','CustomIconTint':'FFFFFF','Shape':'ModelEntity'}.items():
   if b.find(f"property[@name='{k}']") is not None:E.SubElement(blocks,'remove',xpath=f"/blocks/block[@name='{n}']/property[@name='{k}']")
   a=E.SubElement(blocks,'append',xpath=f"/blocks/block[@name='{n}']");E.SubElement(a,'property',name=k,value=v)
save('blocks',blocks)
with (C/'Localization.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english'])
 for n,m in names:w.writerow([n,'blocks','','','','Apothecary Supplies' if m=='delveApothecaryChest' else 'Ironbound Supply Chest'])
# Native noise-filtered subbiomes create same-species patches, without touching POIs.
biomes=E.Element('configs');patches=[]
for biome in docs['biomes'].xpath('/worldgeneration/biomes/biome'):
 species=sorted({d.get('blockname') for d in biome.xpath('.//decoration') if d.get('blockname','').startswith('planted') and 'Player' not in d.get('blockname','')})
 for i,n in enumerate(species):
  xp=f"/worldgeneration/biomes/biome[@name='{biome.get('name')}']"
  E.SubElement(biomes,'remove',xpath=xp+f"//decoration[@blockname='{n}']")
  a=E.SubElement(biomes,'append',xpath=xp)
  s=E.SubElement(a,'subbiome',noise='.055, 0, .22',noiseoffset=f'{12000+i*1733}, {19000+i*2357}')
  layers=biome.find('layers')
  assert layers is not None,biome.get('name')
  s.append(copy.deepcopy(layers))
  d=E.SubElement(s,'decorations');E.SubElement(d,'decoration',type='block',blockname=n,prob='.24',rotatemax='3')
  patches.append([biome.get('name'),n])
save('biomes',biomes)
(R/'artifacts/batch-04/content.json').write_text(json.dumps({'recipes':changes,'containers':names,'wild_patches':patches},indent=2))
# The progression gate keys recipes by their exact ingredients. Keep those keys
# synchronized, otherwise the new rune variants disappear from crafting.
def newkey(key):
 parts=key.split('|')
 if len(parts)!=4:return key
 for n,old,new in changes:
  if parts[0]==n.lower():parts[3]=parts[3].replace(old.lower()+'=',new.lower()+'=')
 parts[3]=','.join(sorted(parts[3].split(',')));return '|'.join(parts)
import re
catalog=R/'src/Code/ForestSliceCatalog.generated.cs'
catalog.write_text(re.sub(r'case "([^"]+)"',lambda m:'case "'+newkey(m[1])+'"',catalog.read_text()))
checks=E.parse(str(R/'artifacts/validation/forest-ready/slice-checks.xml'))
for r in checks.getroot():
 if r.get('key'):r.set('key',newkey(r.get('key')))
checks.write(str(R/'artifacts/batch-04/slice-checks.xml'),encoding='utf-8')
print('Batch 4:',len(changes),'rune ingredients,',len(names),'container models,',len(patches),'wild species patches')


