"""Regression checks for first-tier equipment definitions."""
from pathlib import Path
from xml.etree import ElementTree as E

root = Path(__file__).resolve().parents[1]
items = E.parse(root/'src/Delve/Config/items.xml')
checks = 0
def check(value, message):
    global checks
    assert value, message
    checks += 1

# An effect_group on a derived item replaces inherited groups. Prototype
# modifiers therefore must retain the native base stats explicitly.
for name in ['delveLeatherKnuckles', 'delveBoneDagger', 'delveOakCudgel',
             'delveAshSpear', 'delveBorderBow', 'delveIronDagger',
             'delveIronMace', 'delveIronSpear', 'delveHuntingBow']:
    item = items.find(f".//item[@name='{name}']")
    for stat in ['DegradationMax', 'DegradationPerUse']:
        check(item.find(f".//passive_effect[@name='{stat}'][@operation='base_set']") is not None,
              f'{name} missing inherited {stat}')
    if 'Bow' not in name:
        for stat in ['EntityDamage', 'StaminaLoss']:
            check(item.find(f".//passive_effect[@name='{stat}'][@operation='base_set']") is not None,
                  f'{name} missing inherited {stat}')

for slot in ['Helmet','Outfit','Gloves','Boots']:
    item = items.find(f".//item[@name='armorDelvePadded{slot}']")
    check(item is not None, 'Missing padded cloth option')
    for stat, negative in [('Mobility',True),('StaminaChangeOT',True),('NoiseMultiplier',False)]:
        effects = item.findall(f".//passive_effect[@name='{stat}']")
        check(any((float(e.get('value')) < 0 if negative else float(e.get('value')) > 0) for e in effects),
              f'Padded {slot} has no {stat} contribution for light fundamentals')

result = f'PASS: {checks} first-tier equipment regression checks.'
(root/'artifacts/validation/first-tier-equipment.txt').write_text(result+'\n')
print(result)
