"""Validate actual engine-merged XML, not merely authored patches."""
from pathlib import Path
from lxml import etree as E
import json
root=Path(__file__).resolve().parents[1]
evidence=root/'artifacts/validation/recipe-learning'
report=json.loads((evidence/'audit.json').read_text())
config=E.parse(str(root/'playtest/RecipeLearning/serverconfig.xml'))
game=config.find("property[@name='GameName']").get('value')
dump=root/'playtest/RecipeLearning/Saves/Allium-v0.10'/game/'ConfigsDump'
items=E.parse(str(dump/'items.xml'))
ids={n.get('name') for n in items.xpath('/items/item[property[@name="Tags" and contains(@value,"delveRetiredMagazine")]]')}
assert len(ids)==26,len(ids)
for name in ids:
    n=items.find(f"item[@name='{name}']")
    assert not n.xpath('.//triggered_effect[@action="AddProgressionLevel"]')
    assert not n.xpath('.//property[@name="Class" and (@value="Eat" or @value="OpenLootBundle")]')
for kind in ('loot','traders'):
    d=E.parse(str(dump/(kind+'.xml')))
    assert not [n for n in d.xpath('//item') if n.get('name') in ids]
quests=E.parse(str(dump/'quests.xml'))
assert not [n for n in quests.xpath('//reward') if n.get('id') in ids or 'skillmagazine' in n.get('id','').lower()]
challenge=E.parse(str(dump/'challenges.xml')).find("challenge[@name='readMagazines']/objective")
assert challenge.get('type')=='Craft' and challenge.get('item')=='meleeToolRepairT0StoneAxe'
for name in ('delveLessonFarmingNotes','delveLessonCookingNotes','delveLessonMiningNotes','delveLessonSmithingNotes','delveLessonCarpentryNotes','delveLessonAlchemyNotes'):
    assert items.find(f"item[@name='{name}']") is not None
text='PASS: engine-merged loot/vendors/rewards contain no crafting magazines; 26 legacy definitions grant no crafting levels; replacement crafting challenge and all six lesson tomes are present.\n'
(evidence/'merged-runtime.txt').write_text(text)
print(text)
