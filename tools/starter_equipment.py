"""Playable starter equipment; native meshes/rigs, independent Delve balance."""
from copy import deepcopy


def extend(vanilla, items, buffs, node, prop, effect, loc, recipe):
    def native(name):
        source = vanilla['items'].find(f".//item[@name='{name}']")
        assert source is not None, name
        parent = source.find("property[@name='Extends']")
        result = native(parent.get('value')) if parent is not None else {}
        for child in source.findall('property'):
            if child.get('name') != 'Extends':
                result[child.get('class') or child.get('name')] = deepcopy(child)
        return result

    def make(name, parent, title, description):
        # Copy resolved properties, never inherited stats, set bonuses or perks.
        it = node(items, 'item', name=name)
        for child in native(parent).values():
            it.append(child)
        def put(key, value):
            old = it.find(f"property[@name='{key}']")
            if old is not None: it.remove(old)
            prop(it, key, value)
        put('CustomIcon', parent)
        put('DescriptionKey', loc(name+'Desc', description))
        put('CreativeMode', 'Player')
        put('UnlockedBy', '')
        put('EconomicValue', 20)
        put('SellableToTrader', 'false')
        loc(name, title)
        return it, put

    # Distinct native rigs keep the full equip, aiming, firing and reload animation.
    magic = [
        ('Wand', 'Wands', 'gunHandgunT0PipePistol', 'Spark Wand', 18, 120, 8, 'delveSpark', 2, 'p_electric_shock'),
        ('Staff', 'Staffs', 'gunRifleT0PipeRifle', 'Ember Staff', 42, 40, 1, 'delveEmberFlash', 2, 'p_onFire'),
        ('Totem', 'Totems', 'gunHandgunT0PipePistol', 'Withering Totem', 10, 60, 4, 'delveWither', 5, 'p_electric_shock'),
    ]
    for tool, skill, parent, title, damage, rpm, capacity, buff, duration, particle in magic:
        name = 'delveStarter'+tool
        rune = 'delve'+tool+'Rune'
        description = f'{title}: uses {tool} Runes. Reload normally. Native firearm model and animations are temporary. '
        description += 'A damaging hex slows enemies by 20% and weakens melee damage by 15% for five seconds.' if tool == 'Totem' else 'Direct magical damage with an animated impact effect; no damage over time.'
        it, put = make(name, parent, title, description)
        put('Tags', f'weapon,ranged,delveWeapon,delveMagic,delve{skill}')
        put('RepairTools', 'resourceWood')
        put('CustomIconTint', '155,110,235')
        action = it.find("property[@class='Action0']")
        action.find("property[@name='Magazine_items']").set('value', rune)
        eg = node(it, 'effect_group', name='Starter magic')
        for stat, value in [('MaxRange',35),('DamageFalloffRange',25),('RoundsPerMinute',rpm),('BurstRoundCount',1),('MagazineSize',capacity),('ReloadSpeedMultiplier',1),('DegradationMax',250),('DegradationPerUse',1),('ModSlots',0),('SpreadDegreesVertical',1),('SpreadDegreesHorizontal',1)]:
            effect(eg, stat, value, 'base_set')
        hit = node(eg, 'triggered_effect', trigger='onSelfAttackedOther', action='AddBuff', target='other', buff=buff)
        node(hit, 'requirement', name='EntityTagCompare', target='other', tags='zombie,animal')
        recipe(name, {'resourceWood':20, 'resourceCloth':5, 'resourceRockSmall':10})
        ammo, put = make(rune, 'ammo9mmBulletBall', tool+' Runes', f'Ammunition for the {title}. Crafted by Alchemy. One rune per cast.')
        put('CustomIcon', 'resourceRockSmall')
        put('CustomIconTint', '155,110,235')
        put('Tags', f'ammo,delveMagic,delve{skill}')
        put('Material', 'Mstone')
        eg = node(ammo, 'effect_group', name='Rune payload', tiered='false')
        effect(eg, 'EntityDamage', damage, 'base_set')
        effect(eg, 'BlockDamage', 1, 'base_set')
        r = recipe(rune, {'resourceRockSmall':5, 'resourceCropChrysanthemumPlant':1})
        r.set('count', '10')
        b = node(buffs, 'buff', name=buff, name_key=loc(buff,title+' Impact'), description_key=loc(buff+'Desc',description), icon='ui_game_symbol_electric_power')
        node(b, 'stack_type', value='replace')
        node(b, 'duration', value=duration)
        eg = node(b, 'effect_group')
        if tool == 'Totem':
            effect(eg, 'WalkSpeed', -.2, 'perc_add')
            effect(eg, 'RunSpeed', -.2, 'perc_add')
            effect(eg, 'EntityDamage', -.15, 'perc_add')
        for trigger in ['onSelfBuffStart', 'onSelfEnteredGame']:
            node(eg, 'triggered_effect', trigger=trigger, action='AttachParticleEffectToEntity', particle=particle, parent_transform='Spine1', local_offset='0,-.2,0')
        for trigger in ['onSelfBuffRemove', 'onSelfDied', 'onSelfLeaveGame']:
            node(eg, 'triggered_effect', trigger=trigger, action='RemoveParticleEffectFromEntity', particle=particle)

    # Healing deliberately bypasses ranged hit processing in HealingTotem.cs.
    it, put = make('delveMendingTotem', 'gunHandgunT0PipePistol', 'Mending Totem',
                   'Self healing: restores 20 base health per Healing Rune. Four runes per load. Wisdom and Totems proficiency improve healing. Full-health casts spend a rune but grant no practice. Native firearm model/animations are temporary.')
    put('Tags', 'weapon,ranged,delveWeapon,delveMagic,delveTotems')
    put('RepairTools', 'resourceWood')
    put('CustomIconTint', '110,230,150')
    it.find("property[@class='Action0']/property[@name='Magazine_items']").set('value', 'delveHealingRune')
    eg = node(it, 'effect_group', name='Mending Totem')
    for stat, value in [('MaxRange',1),('DamageFalloffRange',1),('EntityDamage',0),('BlockDamage',0),('RoundsPerMinute',30),('BurstRoundCount',1),('MagazineSize',4),('ReloadSpeedMultiplier',1),('DegradationMax',250),('DegradationPerUse',1),('ModSlots',0)]:
        effect(eg, stat, value, 'base_set')
    recipe('delveMendingTotem', {'resourceWood':20,'resourceCloth':5,'resourceRockSmall':10})
    ammo, put = make('delveHealingRune','ammo9mmBulletBall','Healing Runes',
                     'Ammunition for the Mending Totem. One rune per self-healing cast. Crafted by Alchemy.')
    put('CustomIcon','resourceRockSmall')
    put('CustomIconTint','110,230,150')
    put('Tags','ammo,delveMagic,delveTotems')
    put('Material','Mstone')
    eg = node(ammo,'effect_group',name='Healing rune',tiered='false')
    effect(eg,'EntityDamage',0,'base_set')
    effect(eg,'BlockDamage',0,'base_set')
    recipe('delveHealingRune',{'resourceRockSmall':5,'resourceCropChrysanthemumPlant':2,'resourceCloth':1}).set('count','10')
    b = node(buffs,'buff',name='delveMendingGlow',name_key=loc('delveMendingGlow','Mending'),description_key=loc('delveMendingGlowDesc','The totem has restored health.'),icon='ui_game_symbol_medical')
    node(b,'stack_type',value='replace')
    node(b,'duration',value=1)
    eg = node(b,'effect_group')
    node(eg,'triggered_effect',trigger='onSelfBuffStart',action='AttachParticleEffectToEntity',particle='p_weatherEffects_freezingBreath',parent_transform='Camera',local_rotation='90,0,0',oneshot='true')

    # Complete four-slot sets with native visual rigs but no native set bonuses.
    for category, source, title, armor, penalty, ingredients, repair in [
        ('Light','Primitive','Wayfarer Cloth',6,0,{'resourceCloth':8,'resourceYuccaFibers':10},'resourceCloth'),
        ('Medium','Biker','Border Leather',9,.025,{'resourceLeather':8,'resourceCloth':4},'resourceLeather'),
        ('Heavy','Raider','Scavenged Iron',12,.05,{'resourceScrapIron':30,'resourceLeather':4},'resourceScrapIron'),
    ]:
        for slot in ['Helmet','Outfit','Gloves','Boots']:
            name = 'armorDelve'+category+slot
            it, put = make(name,'armor'+source+slot,title+' '+slot,f'Starter {category.lower()} armor. {armor} armor per piece. Uses native {source} visuals. No set bonus. Repair with {repair}.')
            tags = it.find("property[@name='Tags']").get('value').split(',')
            tags = [t for t in tags if not t.startswith('armorBiker') and t != 'biomeChallenge']
            put('Tags', ','.join(tags)+',delveArmor')
            put('ArmorGroup', 'delve'+category)
            put('DisplayType', 'armor'+category)
            put('RepairTools', repair)
            eg = node(it,'effect_group',name='Delve starter armor')
            effect(eg,'PhysicalDamageResist',armor)
            effect(eg,'ElementalDamageResist',armor,tags='heat,electrical')
            effect(eg,'DegradationMax',200,'base_set')
            effect(eg,'DegradationPerUse',1,'base_set')
            effect(eg,'ModSlots',1,'base_set')
            if penalty:
                effect(eg,'Mobility',-penalty,'perc_add')
                effect(eg,'StaminaChangeOT',-penalty,'perc_add',tags='running')
                effect(eg,'NoiseMultiplier',penalty*2,'perc_add')
            recipe(name, ingredients)
