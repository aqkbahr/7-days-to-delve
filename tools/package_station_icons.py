"""Add dedicated generated artwork; keep all gameplay content byte-identical."""
from pathlib import Path
from datetime import datetime
from copy import deepcopy
import json,hashlib,shutil,os,sys,html
from PIL import Image
from lxml import etree as E
R=Path('D:/Projects/ChatGPT/7 days to delve')
A=R/'artifacts/station-icon-art';A.mkdir(parents=True,exist_ok=True)
selection=R/'dist/active-playtest-release.json';original=selection.read_bytes()
B=Path(json.loads(original)['release']);m=json.loads((B/'manifest.json').read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
for entry in m['files']:assert sha(B/entry['path'])==entry['sha256'].upper(),entry['path']
spec=json.loads((A/'prompts.json').read_text());assert len(spec['assets'])==15
M=R/'src/ZZZZZZZZZZZZZZZZZZZDelveStationIcons';icons=M/'UIAtlases/ItemIconAtlas';icons.mkdir(parents=True,exist_ok=True)
cfg=M/'Config';cfg.mkdir(exist_ok=True);patch=E.Element('configs');checks=[]
sys.path.insert(0,str(R/'tools'))
from build_station_progression import merge
before=merge(B,'items');after=deepcopy(before)
for row in spec['assets']:
    target=icons/(row['icon']+'.png');shutil.copy2(row['source'],target)
    im=Image.open(target);assert im.mode=='RGBA' and im.getchannel('A').getextrema()==(0,255),row['id']
    assert im.width==im.height and im.width>=256,row['id']
    path="/items/item[@name='%s']/property[@name='CustomIcon']/@value"%row['item']
    nodes=after.xpath(path);assert len(nodes)==1,row['item']
    E.SubElement(patch,'set',xpath=path).text=row['icon'];nodes[0].getparent().set('value',row['icon'])
    checks.append(dict(item=row['item'],icon=row['icon'],size=im.size,alpha=[0,255],sha256=sha(target)))
    # Remove only the icon reference from the comparison; every other item field
    # must be identical to the accepted combined package.
    old=deepcopy(before.xpath('/items/item[@name=$n]',n=row['item'])[0]);new=deepcopy(after.xpath('/items/item[@name=$n]',n=row['item'])[0])
    for node in (old,new):node.remove(node.xpath("property[@name='CustomIcon']")[0])
    assert E.tostring(old,method='c14n')==E.tostring(new,method='c14n')
assert len({r['sha256'] for r in checks})==15
E.ElementTree(patch).write(str(cfg/'items.xml'),pretty_print=True,xml_declaration=True,encoding='utf-8')
(M/'ModInfo.xml').write_text('<xml><Name value="ZZZZZZZZZZZZZZZZZZZDelveStationIcons"/><DisplayName value="Delve Dedicated Station Add-on Icons"/><Version value="0.18.1"/><Author value="Delve"/></xml>')
gallery=['<!doctype html><meta charset="utf-8"><title>Station add-on icons</title><style>body{background:#25221e;color:#eee;font:16px system-ui;margin:30px}main{display:grid;grid-template-columns:repeat(5,1fr);gap:16px}figure{margin:0;padding:12px;background:#36312a;text-align:center}img{width:160px;height:160px;object-fit:contain}small img{width:60px;height:60px}figcaption{margin-top:8px}</style><h1>Station add-on icons</h1><p>Dedicated medieval fantasy art. Each card includes a small inventory-size preview.</p><main>']
for row in spec['assets']:
    url='../src/'+M.name+'/UIAtlases/ItemIconAtlas/'+row['icon']+'.png'
    gallery.append(f'<figure><img src="{html.escape(url)}"><small><img src="{html.escape(url)}"></small><figcaption>{html.escape(row["id"])}</figcaption></figure>')
gallery.append('</main>')
# Gallery lives next to the source directory for simple portable file references.
(R/'artifacts/station-icons-preview.html').write_text(''.join(gallery),encoding='utf-8')
(A/'validation.json').write_text(json.dumps(dict(result='PASS',baseline=str(B),method='Built-in imagegen; original generated PNGs copied without image edits',assets=checks,mechanicsUnchanged=True,clientVisualCheck='Not performed'),indent=2))
N=R/'dist'/('Delve-Station-Icons-'+datetime.now().strftime('%Y%m%d-%H%M%S'));N.mkdir()
for entry in m['files']:
    rel=entry['path'];dest=N/rel;dest.parent.mkdir(parents=True,exist_ok=True)
    if rel.startswith(('Mods/','Worlds/')):os.link(B/rel,dest)
    else:shutil.copy2(B/rel,dest)
shutil.copytree(M,N/'Mods'/M.name)
shutil.copytree(A,N/'Evidence/StationIcons')
notes='STATION ADD-ON ICONS - 0.18.1\n15 dedicated transparent medieval fantasy inventory icons replace placeholders.\nRecipes, progression, stations, saves and all existing gameplay modules are unchanged.\nContinue your current save after restarting the game.\n'
(N/'STATION-ICONS.txt').write_text(notes)
(N/'START-HERE.txt').write_text(notes+'\n'+(B/'START-HERE.txt').read_text(encoding='utf-8-sig'),encoding='utf-8')
(N/'VALIDATION.txt').write_text('Station icons: PASS 15 unique RGBA assets, transparent alpha, exact item references, metadata-only comparison and package hashes. Artwork visually reviewed; client inventory appearance awaits playtest.\n\n'+(B/'VALIDATION.txt').read_text(encoding='utf-8-sig'),encoding='utf-8')
launch=(N/'Play-Allium.ps1').read_text(encoding='utf-8-sig').replace(m['version'].split('-')[0],'0.18.1');(N/'Play-Allium.ps1').write_text(launch,encoding='utf-8')
m.update(name='7 Days to Delve - Dedicated station add-on icons',version='0.18.1-station-icons')
m['files']=[dict(path=p.relative_to(N).as_posix(),sha256=sha(p)) for p in sorted(N.rglob('*')) if p.is_file() and p!=N/'manifest.json']
(N/'manifest.json').write_text(json.dumps(m,indent=2))
for entry in m['files']:assert sha(N/entry['path'])==entry['sha256'],entry['path']
assert selection.read_bytes()==original,'Active build changed during packaging'
(A/'release.txt').write_text(str(N));(A/'selection-before.json').write_bytes(original)
print('PASS candidate package:',N)
