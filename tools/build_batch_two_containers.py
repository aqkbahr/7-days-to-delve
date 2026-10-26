"""Medieval containers retain the native appliance's storage feature and loot pool."""
from pathlib import Path
from lxml import etree as E
import json,copy,csv
import build_forest_slice as merger
ROOT=Path(__file__).resolve().parents[1]
merger.MOD_NAMES=['Delve','DelveWayrest','DelveWildlife','ZDelveDungeons','ZDelveForest','ZDelveRecruits','ZDelvePresentation','ZZZDelveBatch01']
doc=merger.merge(ROOT/'src','blocks');blocks={x.get('name'):x for x in doc.getroot() if x.tag=='block'}
def inherited(name,path,seen=()):
    if name in seen:return None
    b=blocks[name];v=b.find(path)
    if v is not None:return v
    parent=b.find('property[@name="Extends"]')
    return inherited(parent.get('value'),path,seen+(name,)) if parent is not None and parent.get('value') in blocks else None
root=E.Element('configs');append=E.SubElement(root,'append',xpath='/blocks');mapping=[]
terms=('fridge','cooler','microwave','toaster','coffeemaker','stove','grill','washer','dryer','laundry','toilet','bathtub','sink','vending','gasrange','walloven','dishwasher','oven','appliance')
for name in sorted(blocks):
    if not any(t in name.lower() for t in terms) or name.startswith('delve'):continue
    feature=inherited(name,'property[@class="CompositeFeatures"]')
    if feature is None or feature.find('property[@class="TEFeatureStorage"]') is None:continue
    storage=feature.find('property[@class="TEFeatureStorage"]')
    loot=storage.find('property[@name="LootList"]')
    if loot is None:continue
    identifier='delveMedieval_'+name
    b=E.SubElement(append,'block',name=identifier)
    for k,v in [('Extends','wineBarrelPlayer'),('CreativeMode','None'),('CustomIcon','delveFermentingBarrel'),('DescriptionKey','delveMedievalContainerDesc'),('CanPickup','false')]:E.SubElement(b,'property',name=k,value=v)
    features=E.SubElement(b,'property',{'class':'CompositeFeatures'});features.append(copy.deepcopy(storage))
    mapping.append(dict(source=name,target=identifier,loot=loot.get('value')))
out=ROOT/'src/ZZZZDelveBatch02/Config'
(out/'medieval-containers.xml').write_bytes(E.tostring(root,pretty_print=True))
# blocks.xml is the actual loader entry; the content overlay currently has no block changes.
(out/'blocks.xml').write_bytes(E.tostring(root,pretty_print=True))
(ROOT/'artifacts/batch-02/container-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
mapxml=E.Element('containers')
for row in mapping:E.SubElement(mapxml,'container',**row)
(ROOT/'artifacts/batch-02/container-map.xml').write_bytes(E.tostring(mapxml,pretty_print=True))
with (out/'Localization.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english']);w.writerow(['delveMedievalContainerDesc','blocks','Block','','','A wooden storage barrel. Search it for supplies.'])
    for row in mapping:w.writerow([row['target'],'blocks','Block','','','Supply Barrel'])
print('Prepared',len(mapping),'appliance replacements with original storage pools')
storage_names=[]
for name in blocks:
    feature=inherited(name,'property[@class="CompositeFeatures"]')
    if feature is not None and feature.find('property[@class="TEFeatureStorage"]') is not None:storage_names.append(name)
storage_names.extend(r['target'] for r in mapping)
(ROOT/'artifacts/batch-02/storage-blocks.txt').write_text('\n'.join(sorted(storage_names)))
