from pathlib import Path
from lxml import etree as E
from PIL import Image
import json,copy
import build_forest_slice as merge
R=Path(__file__).resolve().parents[1];M='ZZZZZZZDelveBatch04';count=0
def check(b,msg):
 global count
 assert b,msg
 count+=1
merge.MOD_NAMES=sorted(p.name for p in (R/'artifacts/batch-04/candidate/Mods').iterdir() if p.name!=M)
root=R/'artifacts/batch-04/candidate/Mods'
before={k:merge.merge(root,k) for k in ('blocks','loot','recipes','biomes')}
merge.MOD_NAMES.append(M);after={k:merge.merge(root,k) for k in before}
check(not after['loot'].xpath("//item[@name='oldCash']"),'paper money removed')
expected=copy.deepcopy(before['loot'])
for i in expected.xpath("//item[@name='oldCash']"):i.set('name','resourcePaper')
check(E.tostring(expected)==E.tostring(after['loot']),'loot quantities/probabilities preserved')
report=json.loads((R/'artifacts/batch-04/content.json').read_text())
for n,m in report['containers']:
 b=copy.deepcopy(before['blocks'].xpath(f"/blocks/block[@name='{n}']")[0]);a=copy.deepcopy(after['blocks'].xpath(f"/blocks/block[@name='{n}']")[0])
 for obj in (a,b):
  for p in list(obj):
   if p.get('name') in ('Model','CustomIcon','TintColor','CustomIconTint','Shape'):obj.remove(p)
 check(E.tostring(a)==E.tostring(b),'container gameplay retained '+n)
for n in ('delveTotemRune','delveMooncapTotemRune','delveHealingRune','delveEtchedHexRune','delveEtchedHealingRune'):
 check([E.tostring(x) for x in before['recipes'].xpath(f"/recipes/recipe[@name='{n}']")]==[E.tostring(x) for x in after['recipes'].xpath(f"/recipes/recipe[@name='{n}']")],'totem retained '+n)
for biome,n in report['wild_patches']:
 rows=after['biomes'].xpath(f"/worldgeneration/biomes/biome[@name='{biome}']//decoration[@blockname='{n}']")
 check(len(rows)==1,'one noise patch per species '+n)
 sub=rows[0].getparent().getparent();check(sub.tag=='subbiome' and sub.get('noise') is not None,'cluster noise '+n)
 check(len(sub.findall('layers/layer'))>=4,'complete terrain layers '+n)
 check(len(sub.findall('decorations/decoration'))==1,'single species in patch '+n)
for b in after['blocks'].xpath("/blocks/block[starts-with(@name,'plantedDelve')]"):
 check(b.find("property[@name='DisplayInfo']").get('value')=='None','plant hover suppressed '+b.get('name'))
for n in ('delveApothecaryChest','delveIronboundChest'):
 im=Image.open(root/M/'UIAtlases/ItemIconAtlas'/f'{n}.png').convert('RGBA');check(len(set(im.getdata()))>100,'rendered icon '+n)
for file in ('ProgressionScreen.cs','RecruitScreen.cs'):
 source=(R/'src/Code'/file).read_text();check('mouse==0' not in source and 'b==0' not in source,'native left-click convention '+file)
out=f'PASS {count} Batch 4 content assertions: exact loot replacement; container gameplay; totems; terrain-backed same-species clusters; plant labels; rendered icons; native input convention.\n'
(R/'artifacts/batch-04/content-validation.txt').write_text(out);print(out)
