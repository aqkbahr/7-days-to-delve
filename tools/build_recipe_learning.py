"""Audit frozen Allium recipes and retire vanilla crafting magazines safely."""
from pathlib import Path
from copy import deepcopy
from lxml import etree as E
import json, csv

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config')
release=Path((ROOT/'artifacts/recipe-learning-base.txt').read_text(encoding='utf-8-sig').strip())
out=ROOT/'src/ZZZZZZZZDelveRecipeLearning';(out/'Config').mkdir(parents=True,exist_ok=True)
evidence=ROOT/'artifacts/validation/recipe-learning';evidence.mkdir(parents=True,exist_ok=True)

def apply(doc,patch):
    for op in patch:
        if not isinstance(op.tag,str):continue
        targets=doc.xpath(op.get('xpath'));assert targets,(op.tag,op.get('xpath'))
        for t in targets:
            if op.tag=='append':
                for c in op:t.append(deepcopy(c))
            elif op.tag=='set':
                if getattr(t,'is_attribute',False):t.getparent().set(t.attrname,op.text or '')
                else:t.text=op.text or ''
            elif op.tag=='remove':
                if getattr(t,'is_attribute',False):del t.getparent().attrib[t.attrname]
                else:t.getparent().remove(t)
            elif op.tag in ('insertBefore','insertAfter'):
                for c in op:(t.addprevious if op.tag=='insertBefore' else t.addnext)(deepcopy(c))
            else:raise AssertionError(op.tag)

docs={}
for kind in ('items','blocks','recipes','loot','traders','quests','challenges'):
    d=E.parse(str(BASE/(kind+'.xml')))
    for mod in sorted((release/'Mods').iterdir()):
        f=mod/'Config'/(kind+'.xml')
        if f.exists():apply(d,E.parse(str(f)).getroot())
    docs[kind]=d
before={k:deepcopy(v) for k,v in docs.items()}
patches={k:E.Element('configs') for k in docs}
def op(kind,tag,xpath,text=None):
    n=E.SubElement(patches[kind],tag,xpath=xpath);n.text=text;return n
def prop(node,name,value):E.SubElement(node,'property',name=name,value=str(value))

magazines={n.get('name') for n in docs['items'].xpath('//item') if n.get('name','').endswith('SkillMagazine')}
magazines.add('questRewardT1SkillMagazineBundle')
assert len(magazines)==27
names=' or '.join("@name='%s'"%n for n in sorted(magazines))
localization=[]
retired=magazines-{'masterSkillMagazine'} # Hidden shared template also serves admin perk books.
for name in sorted(retired):
    op('items','remove',f"/items/item[@name='{name}']/*")
    it=op('items','append',f"/items/item[@name='{name}']")
    for k,v in {'Extends':'resourcePaper','CustomIcon':'resourcePaper','CreativeMode':'None','EconomicValue':'0','SellableToTrader':'false','DescriptionKey':'delveRetiredMagazineDesc','Tags':'paper,delveRetiredMagazine'}.items():prop(it,k,v)
    localization.append((name,'Recovered paper'))
localization.append(('delveRetiredMagazineDesc','Obsolete crafting pages. Scrap for paper. Crafting recipes now use your related proficiency; these pages grant no skill levels.'))
removed={}
for kind in ('loot','traders'):
    matches=docs[kind].xpath('//*['+names+']')
    # Only entry references, never group definitions.
    matches=[n for n in matches if n.tag=='item']
    removed[kind]=len(matches)
    if matches:op(kind,'remove','//item['+names+']')
    preview=deepcopy(docs[kind]);apply(preview,patches[kind])
    # Keep referenced groups legal and nonempty after magazine-only pools vanish.
    for group in preview.xpath('//lootgroup | //trader_item_group'):
        if not group.findall('item') and before[kind].xpath(f"//{group.tag}[@name='{group.get('name')}']/item"):
            a=op(kind,'append',f"//{group.tag}[@name='{group.get('name')}']")
            E.SubElement(a,'item',name='resourcePaper',count='1,3')

# Dedicated magazine rewards become modest gold rewards; mixed book pools keep
# their non-magazine entries. Legacy bundle IDs remain loadable as paper.
reward_count=0
reward_ids=set()
for reward in docs['quests'].xpath('//reward'):
    ident=reward.get('id','')
    if ident in magazines or 'skillmagazine' in ident.lower():
        reward_ids.add(ident)
        replacement=deepcopy(reward)
        replacement.set('type','Item');replacement.set('id','casinoCoin');replacement.set('value','100')
        op('quests','append',docs['quests'].getpath(reward.getparent())).append(replacement)
        reward_count+=1
if reward_ids:op('quests','remove','//reward['+' or '.join("@id='%s'"%n for n in sorted(reward_ids))+']')

# The native mandatory magazine lesson must not become an impossible challenge.
challenge="/challenges/challenge[@name='readMagazines']"
op('challenges','remove',challenge+'/objective')
E.SubElement(op('challenges','append',challenge),'objective',type='Craft',item='meleeToolRepairT0StoneAxe',count='1')
for key,value in [('challengeReadMagazines','Practice a craft'),('challengeReadMagazinesHint1','Gather wood, stone and plant fibers, then craft a stone axe.'),('challengeReadMagazinesShort','Craft a stone axe to practice Carpentry.'),('challengeReadMagazinesDesc','Recipes unlock through proficiency gained by doing related work. Craft a stone axe to begin practicing Carpentry. No skill magazine is required.')]:localization.append((key,value))

catalogue=json.loads((release/'Catalogue/first-playtest.json').read_text(encoding='utf-8-sig'))
def signature(r):
    ins=sorted(i.get('name').lower()+'='+str(int(i.get('count'))) for i in r.findall('ingredient'))
    return '|'.join([r.get('name').lower(),r.get('craft_area','').lower(),r.get('count','1'),','.join(ins)])
active={r['key']:r for r in catalogue['recipes']}
schematics={n.get('name') for n in docs['items'].xpath('/items/item') if 'schematic' in n.get('name','').lower() and n.get('name') not in magazines}
rows=[];found=set();cleared=[]
for recipe in docs['recipes'].xpath('/recipes/recipe'):
    key=signature(recipe);row=active.get(key)
    rows.append(dict(key=key,name=recipe.get('name'),status='proficiency' if row else 'deferred-outside-Forest-slice',skill=row['skill'] if row else None,rank=row['rank'] if row else None,tags=recipe.get('tags',''),station=recipe.get('craft_area',''),tool=recipe.get('craft_tool','')))
    if row:
        found.add(key)
        tags=[t for t in recipe.get('tags','').split(',') if t and t!='learnable']
        if 'learnable' in recipe.get('tags','').split(','):op('recipes','set',docs['recipes'].getpath(recipe)+'/@tags',','.join(tags));cleared.append(key)
assert found==set(active),set(active)-found
cleared_hints=[]
for name in sorted({r['name'] for r in active.values()}):
    for kind in ('items','blocks'):
        path=f"/{kind}/{kind[:-1]}[@name='{name}']/property[@name='UnlockedBy']/@value"
        for value in docs[kind].xpath(path):
            if value:
                op(kind,'remove',path.rsplit('/@',1)[0])
                prop(op(kind,'append',f"/{kind}/{kind[:-1]}[@name='{name}']"),'UnlockedBy','')
                cleared_hints.append(name)

for kind,patch in patches.items():
    if len(patch):
        apply(docs[kind],patch)
        E.ElementTree(patch).write(str(out/'Config'/(kind+'.xml')),encoding='utf-8',xml_declaration=True,pretty_print=True)
for kind in ('loot','traders'):assert not docs[kind].xpath('//item['+names+']')
for name in retired:
    it=docs['items'].find(f"item[@name='{name}']")
    assert it.find("property[@name='Extends']").get('value')=='resourcePaper' and not it.findall('effect_group')
for name in schematics:
    assert E.tostring(before['items'].find(f"item[@name='{name}']"))==E.tostring(docs['items'].find(f"item[@name='{name}']")),name
for r in docs['recipes'].xpath('/recipes/recipe'):
    if signature(r) in active:assert 'learnable' not in r.get('tags','').split(',')
    else:
        original=next(n for n in before['recipes'].xpath('/recipes/recipe') if signature(n)==signature(r))
        assert E.tostring(original)==E.tostring(r),'Deferred/special recipe modified: '+signature(r)
for n in before['items'].xpath('/items/item'):
    name=n.get('name')
    if name.startswith('book') or name.startswith('delveLesson'):assert E.tostring(n)==E.tostring(docs['items'].find(f"item[@name='{name}']")),name
with (out/'Config/Localization.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english'])
    for key,value in localization:w.writerow([key,'items','Item','false','false',value])
(out/'ModInfo.xml').write_text('<xml><Name value="DelveRecipeLearning"/><DisplayName value="Delve Proficiency Recipe Learning"/><Version value="1.0.0"/><Author value="Delve"/><Description value="Proficiency recipes; retired crafting magazines; preserved special schematics."/></xml>')
report=dict(result='PASS',base=str(release),active_variants=len(active),audited_variants=len(rows),magazine_ids=len(magazines),retired_item_definitions=len(retired),removed_sources=removed,replaced_quest_rewards=reward_count,preserved_schematic_definitions=len(schematics),cleared_recipe_gates=cleared,cleared_magazine_ui_hints=cleared_hints,recipes=rows)
(evidence/'audit.json').write_text(json.dumps(report,indent=2))
checks=E.Element('slice')
for row in active.values():E.SubElement(checks,'recipe',key=row['key'],name=row['name'],skill=row['skill'] or '',rank=str(row['rank']))
E.ElementTree(checks).write(str(evidence/'slice-checks.xml'),encoding='utf-8',pretty_print=True)
print(json.dumps({k:v for k,v in report.items() if k!='recipes'},indent=2))
