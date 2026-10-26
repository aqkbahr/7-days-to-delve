"""Validate authored weapon contracts and emit a local visual-review gallery."""
import json, html
from pathlib import Path
from PIL import Image
import numpy as np
root=Path(__file__).resolve().parents[2]
out=root/'artifacts/weapon-quality-v2';source=root/'src/Art/ForestWeapons'
old=json.loads((out/'before/catalogue.json').read_text());new=json.loads((source/'catalogue.json').read_text())
prior={x['id']:x for x in old['weapons']}
assert old['aliases']==new['aliases']
assert set(prior)=={x['id'] for x in new['weapons']}
rows=[]
for asset in new['weapons']:
    assert asset['bones']==prior[asset['id']]['bones'],asset['id']
    assert asset['animations']==prior[asset['id']]['animations'],asset['id']
    counts=list(asset['triangles'].values());assert 0<counts[2]<counts[1]<counts[0]<16000
    rows.append(f"{asset['id']} triangles={counts} contract=PASS")
for name in ('Atlas','Normal','Metallic','Occlusion','Emission'):
    assert Image.open(source/f'ForestWeapon{name}.png').size==(2048,2048)
metal=np.asarray(Image.open(source/'ForestWeaponMetallic.png'))[::-1]
assert metal.shape[2]==4 and metal[:512,:512,0].max()==0
assert metal[:512,1024:1536,0].mean()>200 and metal[:,:,3].min()<metal[:,:,3].max()
(out/'contract-check.txt').write_text('PASS 37 models; unchanged aliases, bones, clips; descending LODs; five 2K PBR maps; wood/metal separation\n'+'\n'.join(rows))
cards=[]
for asset in new['weapons']:
    name=html.escape(asset['name']);aid=asset['id']
    imgs=''.join(f'<a href="../forest-weapons/QualityReview/{aid}/view-{i}.png"><img loading="lazy" src="../forest-weapons/QualityReview/{aid}/view-{i}.png" alt="{name}, view {i+1}"></a>' for i in range(3))
    cards.append(f'<section><h2>{name}</h2><p>{asset["tier"]} · {asset["family"]} · {asset["triangles"]["Weapon_LOD0"]:,} triangles</p><div>{imgs}</div></section>')
(out/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>Forest weapon art review</title><style>body{background:#101519;color:#e9e4d8;font:16px system-ui;margin:40px auto;max-width:1400px;padding:0 24px}h1{font-size:36px}h2{margin-bottom:4px}p{color:#c2b9a7}section{border-top:1px solid #45515b;padding:24px 0}section div{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}img{width:100%;border-radius:8px}a{color:#c8dbe8}</style><h1>Forest weapons · material and construction pass</h1><p>20 weapons and magical focuses, 13 rune tokens, 4 ammunition variants. Three Unity views each. These are asset review renders; player-hand fitting and gameplay input testing remain separate.</p>'+''.join(cards),encoding='utf-8')
print('PASS 37 contracts, LOD budgets and PBR maps; review gallery generated')
