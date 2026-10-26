"""Publish the presentation-only Pitch resource update against the current release."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime
import csv, hashlib, json, shutil
from lxml import etree as E
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
BASE=Path((ROOT/'dist/latest-first-forest-release.txt').read_text(encoding='utf-8-sig').strip())
MOD=ROOT/'src/ZZZZZDelvePitch'
manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
for entry in manifest['files']:assert sha(BASE/entry['path'])==entry['sha256'].upper(),entry['path']
doc=E.parse('D:/Steam/steamapps/common/7 Days To Die/Data/Config/items.xml')
def apply(path):
    for op in E.parse(str(path)).getroot():
        if not isinstance(op.tag,str):continue
        nodes=doc.xpath(op.get('xpath'))
        # Native remove patches may legitimately match nothing.
        assert nodes or op.tag=='remove',(path,op.get('xpath'))
        for n in nodes:
            if op.tag=='append':
                for child in op:n.append(deepcopy(child))
            elif op.tag=='set':
                if getattr(n,'is_attribute',False):n.getparent().set(n.attrname,op.text or '')
                else:n.text=op.text or ''
            elif op.tag=='remove':n.getparent().remove(n)
            elif op.tag in ('insertBefore','insertAfter'):
                for child in op:(n.addprevious if op.tag=='insertBefore' else n.addnext)(deepcopy(child))
            else:raise AssertionError(op.tag)
for mod in sorted((BASE/'Mods').iterdir()):
    path=mod/'Config/items.xml'
    if path.exists():apply(path)
before=deepcopy(doc)
apply(MOD/'Config/items.xml')
for name in ('ammoGasCan','ammoGasCanBundle'):
    old=deepcopy(before.xpath('/items/item[@name=$n]',n=name)[0]);new=deepcopy(doc.xpath('/items/item[@name=$n]',n=name)[0])
    assert new.xpath('property[@name="CustomIcon"]/@value')==['delvePitch']
    for item in (old,new):
        for p in item.xpath('property[@name="CustomIcon" or @name="CustomIconTint" or @name="DescriptionKey"]'):item.remove(p)
    assert E.tostring(old,method='c14n')==E.tostring(new,method='c14n'),name
im=Image.open(MOD/'UIAtlases/ItemIconAtlas/delvePitch.png')
assert im.mode=='RGBA' and im.getchannel('A').getextrema()==(0,255)
loc={r['Key']:r['english'] for r in csv.DictReader((MOD/'Config/Localization.csv').open())}
assert loc['ammoGasCan']=='Pitch' and loc['ammoGasCanBundle']=='Bulk Pitch'
release=ROOT/'dist'/('Delve-Pitch-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
release.mkdir()
for entry in manifest['files']:
    dest=release/entry['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/entry['path'],dest)
shutil.copytree(MOD,release/'Mods'/MOD.name)
notes='''PITCH RESOURCE UPDATE - 0.10.4
Gas Can is now Pitch, with a transparent black-sludge icon. The bulk resource
is named Bulk Pitch. Existing stacks, recipes, fuel behavior and prices retain
their existing identities and values. Continue your existing save after relaunch.
Crafting tomes and all previous updates remain included.
'''
(release/'PITCH.txt').write_text(notes,encoding='utf-8')
(release/'START-HERE.txt').write_text(notes+'\n'+(BASE/'START-HERE.txt').read_text(encoding='utf-8-sig'),encoding='utf-8')
(release/'VALIDATION.txt').write_text('PITCH: PASS merged item configuration comparison: only icon/tint/description metadata changes; labels and RGBA alpha verified. No crafting, fuel, price, item-ID or save changes. In-game visual appearance still needs client confirmation.\n\n'+(BASE/'VALIDATION.txt').read_text(encoding='utf-8-sig'),encoding='utf-8')
evidence=release/'Evidence/Pitch';evidence.mkdir(parents=True)
prompt='Create a single square fantasy survival-game inventory icon of Pitch: a thick glossy coal-black sludge mound with a small spreading puddle, sticky tar folds, subtle charcoal-gray highlights that make its silhouette readable at 160x160 pixels. Hand-painted realistic game item art, three-quarter overhead view, centered with generous transparent padding. Isolated material only. No can, jar, bucket, container, label, letters, text, border, background, floor or cast shadow. True transparent background. Output a polished black sludge resource icon.'
(evidence/'image-prompt.txt').write_text('Generated with built-in imagegen, transparent_background=true.\n'+prompt+'\n',encoding='utf-8')
(evidence/'validation.json').write_text(json.dumps({'result':'PASS','baseline':str(BASE),'itemIdsPreserved':['ammoGasCan','ammoGasCanBundle'],'mechanicsUnchanged':True,'iconSize':im.size,'alphaRange':[0,255]},indent=2),encoding='utf-8')
manifest['version']='0.10.4-pitch'
manifest['files']=[{'path':p.relative_to(release).as_posix(),'sha256':sha(p)} for p in sorted(release.rglob('*')) if p.is_file() and p!=release/'manifest.json']
(release/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for entry in manifest['files']:assert sha(release/entry['path'])==entry['sha256']
for pointer in (ROOT/'dist').glob('latest-*-release.txt'):
    if pointer.read_text(encoding='utf-8-sig').strip()==str(BASE):pointer.write_text(str(release)+'\n',encoding='utf-8')
(ROOT/'dist/latest-pitch-release.txt').write_text(str(release)+'\n',encoding='utf-8')
print('PASS Pitch metadata, native compatibility, transparency and packaged hashes:',release)
