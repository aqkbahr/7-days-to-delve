from pathlib import Path
import json,html,hashlib,collections
from PIL import Image,ImageDraw
root=Path('D:/AlliumArt/QualityPass20261025')
models=json.loads((root/'inventory.json').read_text())['models']
cards=[]
for m in models:
    native=m['group'] in ('enemies','quadrupeds','thornback')
    folder=root/('NativeReview' if native else 'Review')
    folder=folder/m['id'] if native else folder/m['group']/m['id']
    if not (folder/'view-0.png').exists():folder=root/'Review'/m['group']/m['id']
    pics=''.join('<a href="'+p.relative_to(root).as_posix()+'"><img loading="lazy" src="'+p.relative_to(root).as_posix()+'"></a>' for p in sorted(folder.glob('view-*.png')))
    label='Native body + details; normalized preview shader' if native and folder.parent.name=='NativeReview' else 'Custom details only' if native else m['group']
    cards.append('<article><h2>'+html.escape(m['id'])+'</h2><p>'+label+'</p><div>'+pics+'</div></article>')
header='''<!doctype html><meta charset="utf-8"><title>Forest asset quality review</title><style>body{background:#151b20;color:#e1e5e8;font:16px system-ui;margin:32px}h1{font-size:30px}h2{font-size:18px}article{background:#202a32;padding:18px;margin:20px 0}article div{display:flex}img{width:100%;max-width:400px}a{color:#92cddd}p{max-width:1000px;line-height:1.5}</style><h1>Forest asset quality review — staged</h1><p>194 model records. Original material maps, surface depth, color variation, wear and detail additions. Creature foundations use the installed game's native bodies and custom detail layers. Native creature previews use normalized shaders for offline viewing; they are not in-game appearance certification.</p><p>Staged only. The 10 creature detail bundles require the paired presentation runtime. No changes were made to the running game. Structural checks pass; hands-on combat, movement, clipping under animation, multiplayer, performance and artistic parity remain unverified in game.</p>'''
(root/'gallery.html').write_text(header+'\n'.join(cards),encoding='utf-8')
files=list((root/'Bundles').glob('*.unity3d'))+[root/'Runtime/DelvePresentation.dll']
manifest={str(p.relative_to(root)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files}
(root/'Reports/delivery-hashes.json').write_text(json.dumps(manifest,indent=2))
counts=collections.Counter(m['group'] for m in models)
report='''FOREST QUALITY PASS — STAGED DELIVERY

Scope: 194 records, 186 Blender exports plus 8 Unity props; 16 asset bundles.
Groups: COUNT_DATA

Implemented: original PBR surfaces, multiscale color and roughness variation, normal detail, vertex occlusion, detail geometry and regenerated LODs. Native creature bodies replace the simplified custom body meshes; custom armor, growths, horns and identity details remain. Existing effects are preserved, not newly reauthored in this pass.

Validation: see unity-review.txt for per-model skinning, tangents, color, animation sampling, LOD checks and preserved collider counts. Native foundation helper: 14 assertions. See native-review.txt for actual installed native bone correspondence. Previews are static offline renders; native shaders are normalized only in the review scene.

Integration: install all 16 bundles with the paired Runtime/DelvePresentation.dll in a later controlled test deployment. NEVER deploy creature detail-only bundles with the old presentation DLL: it hides native bodies. Compare Runtime/baseline-source-hashes.json against current production sources first; merge the staged native-foundation patch into any newer runtime before compiling. Runtime sources are supplied for that merge. Existing unmarked prefabs keep legacy behavior.

Visual review findings: native anatomy is a substantial improvement. However, the Warden chest/helmet and some other armor remain visibly geometric, and Thornback bark plates are oversized and repetitive. These need further shape and silhouette work before this pass can be called vanilla-quality. Weapons and props have richer surfaces, but structural checks do not establish artistic parity.

Not certified: vanilla artistic parity, animation clipping against native bodies in game, gameplay regressions, multiplayer, memory/FPS, save/reload and ragdoll behavior. Inventory icon refresh is not included. The runtime helper preserves native shaders and textures; shaders lacking supported color properties retain their native colors. The native Fur and Character shaders did not expose the supported tint properties in this check, so those body materials keep their native colors.

No live game/mod files were modified. Sources and local native reference dependencies in UnityProject are development-only. Ship only original custom bundles and the paired runtime; do not distribute native review DLLs, native assets or native-body preview files as game assets.

Gallery: ../gallery.html
Hashes: delivery-hashes.json
'''.replace('COUNT_DATA',json.dumps(dict(counts)))
(root/'Reports/DELIVERY.txt').write_text(report)
# Compact representative review sheet; source renders are unchanged.
chosen=[('weapons','delveBoneDagger'),('weapons','delveBorderBow'),('armor','armorDelveForgedHeavyOutfit'),('props','delveDryingRack')]
canvas=Image.new('RGB',(1200,630),'#172027');draw=ImageDraw.Draw(canvas)
for i,(group,id) in enumerate(chosen):
    p=root/'Review'/group/id/'view-0.png'
    if p.exists():
        im=Image.open(p).convert('RGB');im.thumbnail((300,570));canvas.paste(im,(i*300,(570-im.height)//2));draw.text((i*300+8,580),id,fill='white')
canvas.save(root/'Reports/representative-review.jpg')
print('Packaged',len(models),'records;',len(files),'hashed deliverables')
