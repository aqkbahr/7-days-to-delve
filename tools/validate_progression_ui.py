"""Validate UI patches against the installed game and the full progression registry."""
import argparse,copy,json
from pathlib import Path
from lxml import etree as E
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--game',default='D:/Steam/steamapps/common/7 Days To Die');args=p.parse_args()
merged={};checks=0
for name in ['windows.xml','xui.xml']:
 doc=E.parse(str(Path(args.game)/'Data/Config/XUi_InGame'/name))
 for op in E.parse(str(ROOT/'src/Delve/Config/XUi_InGame'/name)).getroot():
  targets=doc.xpath(op.get('xpath'));assert targets,op.get('xpath')
  for target in targets:
   if op.tag=='append':
    for child in op:target.append(copy.deepcopy(child))
   elif op.tag=='remove':target.getparent().remove(target)
   elif op.tag=='set':
    assert target.is_attribute;target.getparent().set(target.attrname,op.text)
   else:raise AssertionError(op.tag)
   checks+=1
 merged[name]=doc
xui=merged['xui.xml'];windows=merged['windows.xml']
group=xui.xpath("/xui/window_group[@name='skills']")[0]
assert [w.get('name') for w in group]==['delveProgression']
assert group.get('controller')=='Delve.XUiC_ProgressionGroup, Delve'
legacy=xui.xpath("/xui/window_group[@name='delveKnowledge']")[0]
assert legacy.get('controller')=='XUiC_SkillWindowGroup'
assert len(legacy)==6
for w in legacy:assert windows.xpath('/windows/window[@name=$name]',name=w.get('name'))
screen=windows.xpath("/windows/window[@name='delveProgression']")[0]
names=[x.get('name') for x in screen.iter() if x.get('name')]
assert len(names)==len(set(names)), 'Duplicate control IDs'
for prefix,count in [('dg_tab',5),('dg_skill',8),('dg_attribute',6),('dg_node',14),('dg_mastery',6)]:
 for i in range(count):assert prefix+str(i) in names;checks+=1
from build_progression_ui import CATEGORIES,BRANCHES
trees=json.loads((ROOT/'src/Progression/trees.json').read_text(encoding='utf-8'))
assert sorted(s for cat in CATEGORIES for s in cat)==sorted(t['skill'] for t in trees)
for tree in trees:
 perks=tree['perks'];assert len(BRANCHES[tree['skill']])==3
 assert [p['rank'] for p in perks[:14]]==[10,10]+[20,40,60,80]*3
 assert 1<=len(perks[14:])<=6 and all(p['rank']==100 for p in perks[14:])
 checks+=3
out=ROOT/'artifacts/validation';out.mkdir(parents=True,exist_ok=True)
result=f'PASS: {checks} UI patch, navigation, control and tree-layout checks. Client rendering/click-through still required.'
(out/'progression-ui.txt').write_text(result+'\n',encoding='utf-8');print(result)
