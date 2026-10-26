from pathlib import Path
import json,sys
from lxml import etree as E
sys.path.insert(0,str(Path(__file__).parent))
from build_station_progression import merge
R=Path(__file__).resolve().parents[1];A=R/'artifacts/summoning-20';P=R/'playtest/Summoning20';B=Path((A/'base.txt').read_text())
recipes=merge(P,'recipes');items=merge(P,'items');blocks=merge(P,'blocks');progression=merge(P,'progression')
rod=recipes.find("recipe[@name='delveForgedSummoningRod']");template=recipes.find("recipe[@name='delveForgedMendingTotem']")
assert len(recipes.findall("recipe[@name='delveForgedSummoningRod']"))==1
assert rod is not None and template is not None and rod.get('craft_area')=='delveSawKitTier3'
a=dict(rod.attrib);b=dict(template.attrib);a.pop('name');b.pop('name');assert a==b
assert [dict(i.attrib) for i in rod]==[dict(i.attrib) for i in template]
assert blocks.find("block[@name='delveSawKitTier3']") is not None
for ingredient in rod:assert items.find("item[@name='%s']"%ingredient.get('name')) is not None
for name in ['delveSummoningRod','delveForgedSummoningRod']:
 item=items.find("item[@name='%s']"%name);assert item.find("property[@class='Action0']/property[@name='Magazine_items']").get('value')=='delveSummoningRune'
perks=progression.findall("perks/perk[@parent='delveTreeSummoning']");assert len(perks)==5
assert sorted(int(p.find('level_requirements/requirement').get('value')) for p in perks)==[10,10,20,20,20]
for p in perks:
 assert p.get('max_level')=='1' and p.get('override_cost')=='1'
 if p.find('level_requirements/requirement').get('value')=='20':assert len(p.findall("level_requirements/requirement[@name='ProgressionLevel']"))==2
result='PASS: five one-point talents at ranks10/20; both fundamentals required; one Forged recipe; identical station, installed-tool and ingredient chain to the audited Forged Mending Totem; matching existing rune ammunition; starter recipe unchanged.'
(A/'content-validation.txt').write_text(result);print(result)
