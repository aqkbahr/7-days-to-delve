from pathlib import Path
import sys
from lxml import etree as E
sys.path.insert(0,str(Path(__file__).parent))
from build_station_progression import merge
R=Path(__file__).resolve().parents[1];P=R/'playtest/Summoning'
items=merge(P,'items');blocks=merge(P,'blocks');recipes=merge(P,'recipes');entities=merge(P,'entityclasses')
names={x.get('name') for x in items.getroot()}|{x.get('name') for x in blocks.getroot()}
rod=items.find("item[@name='delveSummoningRod']");rune=items.find("item[@name='delveSummoningRune']")
assert rod is not None and rune is not None
assert rod.find("property[@class='Action0']/property[@name='Magazine_items']").get('value')=='delveSummoningRune'
for item in [rod,rune]:
 for p in item.iter('property'):
  if p.get('name')=='DropMeshfile':assert p.get('value').startswith('#@modfolder(ZDelvePresentation):')
rows=recipes.findall("recipe[@name='delveSummoningRod']")+recipes.findall("recipe[@name='delveSummoningRune']")
assert len(rows)==3
for recipe in rows:
 assert recipe.get('craft_area') in ['delveFieldCraftingMat','delveInscriptionKit']
 assert recipe.get('craft_area') in names and not recipe.get('craft_tool')
 for ingredient in recipe:assert ingredient.get('name') in names,ingredient.get('name')
boar=entities.find("entity_class[@name='delveSummonedBoar']")
assert boar is not None and len(boar.findall('drop'))==0 and not boar.get('extends')
assert boar.find("property[@name='ExperienceGain']").get('value')=='0'
assert boar.find("property[@name='IsEnemyEntity']").get('value')=='false'
ui=E.parse(str(R/'src/ZZZZZZZZZZZZZZZZZDelveSummoning/Config/XUi_InGame/windows.xml'))
assert ui.find(".//simplebutton[@name='dg_skill8']") is not None
result='PASS merged summoning items, matching rune, explicit bundle references, three station-only recipes, available raw ingredients, no add-on dependency, no inherited harvest drops/XP, allied entity and ninth skill button.'
(R/'artifacts/summoning/content-validation.txt').write_text(result);print(result)
