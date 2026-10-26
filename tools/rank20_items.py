"""Per-item packed food variants; ordinary loot retains its native stack size."""
from copy import deepcopy

PRESERVED = ('foodDelveTrailRations', 'foodDelveTrailRation', 'foodDelveTravelBread',
             'foodDelveBerryPreserve', 'foodDelveHoneyberryCakes')

def extend(items, node, prop, loc, texts):
    for name in PRESERVED:
        original = items.find("item[@name='%s']" % name)
        if original is None:
            raise ValueError('Missing preserved food: ' + name)
        stack = original.find("property[@name='Stacknumber']")
        if stack is None:
            raise ValueError('Packed food requires an explicit base stack: ' + name)
        packed = deepcopy(original)
        packed.set('name', name + 'DelvePacked')
        packed.find("property[@name='Stacknumber']").set('value', str(int(stack.get('value')) * 5 // 4))
        for key, value in [('CreativeMode', 'None'), ('DescriptionKey', name+'DelvePackedDesc')]:
            p = packed.find("property[@name='%s']" % key)
            if p is None: prop(packed, key, value)
            else: p.set('value', value)
        loc(name+'DelvePacked', texts.get(name, name)+' (Packed)')
        loc(name+'DelvePackedDesc', texts.get(name+'Desc', '')+' Prepared with Trail Rations: 25% higher stack capacity. Maker bonuses stay with this food.')
        items.append(packed)
