"""Check starter loadouts against generated output and installed native rigs."""
from pathlib import Path
from xml.etree import ElementTree as E
import json

ROOT = Path(__file__).resolve().parents[1]
items = E.parse(ROOT/'src/Delve/Config/items.xml')
recipes = E.parse(ROOT/'src/Delve/Config/recipes.xml')
buffs = E.parse(ROOT/'src/Delve/Config/buffs.xml')
checks = 0
def check(ok, message):
    global checks
    assert ok, message
    checks += 1
def get(name):
    it = items.find(f".//item[@name='{name}']")
    check(it is not None, 'Missing '+name)
    r = recipes.find(f".//recipe[@name='{name}']")
    check(r is not None and len(r.findall('ingredient')) > 0, 'Missing recipe '+name)
    check(it.find("property[@name='UnlockedBy']").get('value') == '', 'Starter locked '+name)
    return it

for name in ['delveBoneDagger','delveOakCudgel','delveAshSpear','delveBorderBow','delveLeatherKnuckles']:
    get(name)
for tool, skill, buff, capacity in [('Wand','Wands','delveSpark',8),('Staff','Staffs','delveEmberFlash',1),('Totem','Totems','delveWither',4)]:
    it = get('delveStarter'+tool)
    rune = get('delve'+tool+'Rune')
    check(it.find("property[@class='Action0']/property[@name='Magazine_items']").get('value').split(',') == [rune.get('name'), 'delveMooncap'+tool+'Rune'], 'Wrong ammunition')
    check('delve'+skill in it.find("property[@name='Tags']").get('value').split(','), 'Wrong tool skill')
    check('delve'+skill in rune.find("property[@name='Tags']").get('value').split(','), 'Wrong ammo skill')
    check(it.find(".//passive_effect[@name='MagazineSize']").get('value') == str(capacity), 'Wrong capacity')
    check(it.find("property[@name='Extends']") is None and it.find('stats') is None, 'Inherited native balancing')
    check(it.find(".//triggered_effect[@buff='"+buff+"']") is not None, 'Missing impact')
    b = buffs.find(f".//buff[@name='{buff}']")
    check(b is not None and b.find('duration').get('value') != '0', 'Effect never expires')
    check(b.find(".//triggered_effect[@action='AttachParticleEffectToEntity']") is not None, 'No visual')
    check(b.find(".//triggered_effect[@trigger='onSelfBuffRemove']") is not None, 'No visual cleanup')
for category in ['Light','Medium','Heavy']:
    for slot, equipment_slot in [('Helmet','Head'),('Outfit','Chest'),('Gloves','Hands'),('Boots','Feet')]:
        it = get('armorDelve'+category+slot)
        tags = it.find("property[@name='Tags']").get('value').split(',')
        check([tag for tag in tags if tag in ['lightArmor','mediumArmor','heavyArmor']] == [category.lower()+'Armor'], 'Ambiguous armor class')
        check(it.find("property[@name='EquipSlot']").get('value') == equipment_slot, 'Wrong slot')
        check(it.find("property[@class='SDCS']/property[@name='Prefab']") is not None, 'No equipped model')
        check(it.find("property[@name='Extends']") is None, 'Inherited set bonuses')
heal = get('delveMendingTotem')
rune = get('delveHealingRune')
check(heal.find("property[@class='Action0']/property[@name='Magazine_items']").get('value') == 'delveHealingRune,delveMooncapHealingRune', 'Wrong healing ammunition')
check(heal.find(".//passive_effect[@name='MagazineSize']").get('value') == '4', 'Wrong healing capacity')
for stat in ['EntityDamage','BlockDamage']:
    check(rune.find(f".//passive_effect[@name='{stat}']").get('value') == '0', 'Healing rune damages targets')
check(buffs.find(".//buff[@name='delveMendingGlow']") is not None, 'Missing healing effect')
result = {'result':'PASS','checks':checks,'scope':'Starter recipes, loadouts, skill tags, native rigs and effect wiring. Visual/gameplay acceptance remains manual.'}
(ROOT/'artifacts/validation/starter-equipment.json').write_text(json.dumps(result,indent=2))
print(result)
