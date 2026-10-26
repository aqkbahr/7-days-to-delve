"""M3 Forest equipment and spell payloads. Native rigs, explicit Forest recipes."""
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as E
import json
ROOT=Path(__file__).resolve().parents[1]

def extend(vanilla,items,recipes,buffs,node,prop,effect,loc):
    manifest={'recipes':[],'equipment':[],'runes':[]}
    ra=recipes.find("append[@xpath='/recipes']")
    def put(it,key,value):
        old=it.find(f"property[@name='{key}']")
        if old is not None:it.remove(old)
        prop(it,key,value)
    def resolved(name):
        source=items.find(f"item[@name='{name}']")
        if source is None:source=vanilla['items'].find(f"item[@name='{name}']")
        assert source is not None,name
        parent=source.find("property[@name='Extends']")
        result=resolved(parent.get('value')) if parent is not None else E.Element('item')
        for p in source.findall('property'):
            if p.get('name')=='Extends':continue
            attr='class' if p.get('class') else 'name';key=p.get(attr)
            old=result.find(f"property[@{attr}='{key}']")
            if old is not None:result.remove(old)
            result.append(deepcopy(p))
        if source.findall('effect_group'):
            for old in list(result.findall('effect_group')):result.remove(old)
            for eg in source.findall('effect_group'):result.append(deepcopy(eg))
        return result
    def make(name,parent,title,desc,repair=None):
        it=resolved(parent);it.set('name',name);items.append(it)
        for k,v in {'DescriptionKey':name+'Desc','UnlockedBy':'','CreativeMode':'Player','EconomicValue':0,'SellableToTrader':'false','Weight':0}.items():put(it,k,v)
        if repair:put(it,'RepairTools',repair)
        loc(name,title);loc(name+'Desc',desc)
        return it
    def recipe(name,inputs,skill,station,count=1):
        r=node(ra,'recipe',name=name,count=count,craft_time=40,craft_area=station)
        for k,v in inputs.items():node(r,'ingredient',name=k,count=v)
        manifest['recipes'].append(dict(name=name,skill=skill,rank=20,station=station,count=count,ingredients=inputs))
    def durable(it,amount=400):
        eg=node(it,'effect_group',name='Forged durability')
        effect(eg,'DegradationMax',amount,'base_set');effect(eg,'ModSlots',1,'base_set')
    # Real upgrades of existing melee/archery rigs preserve stamina/reach/power attacks.
    for suffix,parent,title,skill,station,inputs,repair in [
      ('Dagger','delveIronDagger','Balanced Iron Dagger','Smithing','delveForgeAnvil',{'resourceForgedIron':10,'delveRoughHandle':1,'delveLeatherBinding':2},'delveMetalRepair'),
      ('Mace','delveIronMace','Balanced Iron Mace','Smithing','delveForgeAnvil',{'resourceForgedIron':12,'delveRoughHandle':2,'delveLeatherBinding':2},'delveMetalRepair'),
      ('Spear','delveIronSpear','Balanced Iron Spear','Smithing','delveForgeAnvil',{'resourceForgedIron':10,'delveSeasonedTimber':3,'delveLeatherBinding':2},'delveMetalRepair'),
      ('Knuckles','delveLeatherKnuckles','Reinforced Handwraps','Carpentry','delveOutfittingKit',{'delveCuredLeather':4,'delveWovenCloth':2,'delveIronFittings':2},'delveHideRepair'),
      ('Bow','delveHuntingBow','Seasoned Longbow','Carpentry','delveSawKit',{'delveSeasonedTimber':6,'delveLeatherBinding':4},'delveFocusRepair'),
      ('Crossbow','gunBowT1IronCrossbow','Border Crossbow','Carpentry','delveSawKit',{'delveSeasonedTimber':6,'delveIronFittings':4,'delveLeatherBinding':4},'delveFocusRepair'),
    ]:
        name='delveForged'+suffix
        it=make(name,parent,title,f'{skill} 20. Forged-grade Forest weapon; native reach, stamina and attack animations. Improved damage and 400 base durability. Repair with {repair}.',repair)
        eg=node(it,'effect_group',name='Forged handling');effect(eg,'EntityDamage',.25,'perc_add');durable(it)
        if suffix=='Crossbow':
            tags=it.find("property[@name='Tags']").get('value');put(it,'Tags',tags+',delveWeapon,delveArchery')
        recipe(name,inputs,skill,station)
        manifest['equipment'].append(dict(name=name,parent=parent,repair=repair,role='Archery' if suffix in ['Bow','Crossbow'] else {'Dagger':'Blades','Mace':'Blunt','Spear':'Polearms','Knuckles':'Unarmed'}[suffix],durability=400))
    for category,material,armor,skill,station in [('Light','delveWovenCloth',9,'Carpentry','delveOutfittingKit'),('Medium','delveCuredLeather',12,'Carpentry','delveOutfittingKit'),('Heavy','resourceForgedIron',15,'Smithing','delveForgeAnvil')]:
        for slot in ['Helmet','Outfit','Gloves','Boots']:
            name='armorDelveForged'+category+slot;parent='armorDelve'+category+slot;repair='delveMetalRepair' if category=='Heavy' else 'delveHideRepair'
            it=make(name,parent,'Forged '+category+' '+slot,f'{skill} 20. {armor} armor per piece; 400 durability. Keeps the starter weight class mobility/noise penalties. No inherited native set bonus. Repair with {repair}.',repair)
            for fx in it.findall('.//passive_effect'):
                if fx.get('name') in ['PhysicalDamageResist','ElementalDamageResist']:fx.set('value',str(armor))
            durable(it);recipe(name,{material:6,'delveLeatherBinding':2},skill,station)
            manifest['equipment'].append(dict(name=name,parent=parent,repair=repair,role=category+'Armor',armor=armor,durability=400))
    for suffix,parent in [('Pickaxe','meleeToolPickT1IronPickaxe'),('Axe','meleeToolAxeT1IronFireaxe'),('Shovel','meleeToolShovelT1IronShovel')]:
        name='delveForged'+suffix
        it=make(name,parent,'Border '+suffix,'Smithing 20. Native iron-tool actions and material bonuses, +25 percentage points block damage, 400 durability. Repair with Metal Repair Supplies.','delveMetalRepair')
        eg=node(it,'effect_group',name='Forged gathering');effect(eg,'BlockDamage',.25,'perc_add');durable(it)
        recipe(name,{'resourceForgedIron':10,'delveRoughHandle':2,'delveLeatherBinding':2},'Smithing','delveForgeAnvil')
        manifest['equipment'].append(dict(name=name,parent=parent,repair='delveMetalRepair',role='Gathering',durability=400))
    for kind,parent,damage in [('Wand','delveWandRune',24),('Staff','delveStaffRune',48),('Hex','delveTotemRune',14),('Healing','delveHealingRune',0),('Ward','delveHealingRune',0)]:
        name='delveEtched'+kind+'Rune'
        it=make(name,parent,'Etched '+kind+' Runes','Alchemy 20. Ten runes per batch at the Inscription Bench. One rune per cast; use with the matching Forged focus.')
        for fx in it.findall('.//passive_effect'):
            if fx.get('name')=='EntityDamage':fx.set('value',str(damage))
            if fx.get('name')=='BlockDamage':fx.set('value','0')
        if kind in ['Healing','Ward','Hex']:put(it,'Tags','ammo,delveMagic,delveTotems')
        recipe(name,{'delveRuneBlank':10,'delveHerbalExtract':2,'delveEmberSalts':1},'Alchemy','delveInscriptionKit',10)
        manifest['runes'].append(dict(name=name,damage=damage,role=kind))
    for suffix,parent,title,capacity,rune,desc in [
      ('Wand','delveStarterWand','Carved Spark Wand',10,'delveEtchedWandRune','Etched runes deal 24 damage with electric impact; 10 shots per load.'),
      ('Staff','delveStarterStaff','Carved Ember Staff',1,'delveEtchedStaffRune','Etched runes deal 48 direct damage plus a 12-damage burst within 2 metres of the struck enemy. No player or terrain splash damage.'),
      ('Totem','delveStarterTotem','Carved Hex Totem',5,'delveEtchedHexRune','Etched runes deal 14 direct damage; hex slows movement by 20% and reduces outgoing damage by 15% for 6 seconds. The existing decay effect also applies.'),
      ('MendingTotem','delveMendingTotem','Carved Mending Totem',5,'delveEtchedHealingRune','Requires Etched Healing Runes. Restores 25 base health, scaled by Wisdom and Totems. Aim at a cooperative player within 12 metres to heal them; otherwise heals yourself. Cannot revive the dead.'),
    ]:
        name='delveForged'+suffix
        it=make(name,parent,title,'Carpentry 20. '+desc+' Uses native firearm animations; repair with Focus Repair Supplies.','delveFocusRepair')
        ammo=it.find("property[@class='Action0']/property[@name='Magazine_items']");ammo.set('value',rune if suffix=='MendingTotem' else ammo.get('value')+','+rune)
        for fx in it.findall('.//passive_effect'):
            if fx.get('name')=='MagazineSize':fx.set('value',str(capacity))
            if suffix=='MendingTotem' and fx.get('name') in ['MaxRange','DamageFalloffRange']:fx.set('value','12')
        if suffix=='Totem':
            for fx in it.findall('.//triggered_effect'):
                if fx.get('buff')=='delveWither':fx.set('buff','delveForgedHex')
        durable(it)
        recipe(name,{'delveSeasonedTimber':6 if suffix=='Staff' else 4,'delveWovenCloth':2,'delveIronFittings':2},'Carpentry','delveSawKit')
        manifest['equipment'].append(dict(name=name,parent=parent,repair='delveFocusRepair',role={'Wand':'Wands','Staff':'Staffs','Totem':'Totems','MendingTotem':'Totems'}[suffix],durability=400,capacity=capacity))
    it=make('delveWardTotem','delveMendingTotem','Protective Totem','Carpentry 20. Etched Ward Runes grant +8 physical and elemental armor for 30 seconds. Aim at a cooperative player within 12 metres, otherwise protects yourself. Recasting refreshes; it does not stack.','delveFocusRepair')
    it.find("property[@class='Action0']/property[@name='Magazine_items']").set('value','delveEtchedWardRune');durable(it)
    for fx in it.findall('.//passive_effect'):
        if fx.get('name') in ['MaxRange','DamageFalloffRange']:fx.set('value','12')
    recipe('delveWardTotem',{'delveSeasonedTimber':4,'delveWovenCloth':2,'delveLeatherBinding':2},'Carpentry','delveSawKit')
    manifest['equipment'].append(dict(name='delveWardTotem',parent='delveMendingTotem',repair='delveFocusRepair',role='Totems',durability=400,capacity=4))
    for name,title,duration,particle,stats in [
      ('delveForgedHex','Withering Hex',6,'p_electric_shock',[('WalkSpeed',-.2,'perc_add'),('RunSpeed',-.2,'perc_add'),('EntityDamage',-.15,'perc_add')]),
      ('delveProtectiveWard','Protective Ward',30,'p_weatherEffects_freezingBreath',[('PhysicalDamageResist',8,'base_add'),('ElementalDamageResist',8,'base_add')]),
      ('delveStaffBurst','Ember Burst',1,'p_onFire',[]),
    ]:
        b=node(buffs,'buff',name=name,name_key=loc(name,title),description_key=loc(name+'Desc',title+': refreshes instead of stacking.'),icon='ui_game_symbol_electric_power')
        node(b,'stack_type',value='replace');node(b,'duration',value=duration);eg=node(b,'effect_group')
        for stat,value,operation in stats:effect(eg,stat,value,operation)
        node(eg,'triggered_effect',trigger='onSelfBuffStart',action='AttachParticleEffectToEntity',particle=particle,parent_transform='Spine1',local_offset='0,-.2,0')
        for trigger in ['onSelfBuffRemove','onSelfDied','onSelfLeaveGame']:node(eg,'triggered_effect',trigger=trigger,action='RemoveParticleEffectFromEntity',particle=particle)
    # A bounded native buff per amount transmits the heal without client-only CVar state.
    for amount in range(1,61):
        name='delveHealPulse'+str(amount)
        b=node(buffs,'buff',name=name,hidden='true')
        node(b,'stack_type',value='replace');node(b,'duration',value=.5)
        eg=node(b,'effect_group')
        node(eg,'triggered_effect',trigger='onSelfBuffStart',action='ModifyStats',stat='Health',operation='add',value=amount)
        node(eg,'triggered_effect',trigger='onSelfBuffStart',action='AddBuff',buff='delveMendingGlow')
    (ROOT/'src/Forest/forged.json').write_text(json.dumps(manifest,indent=2)+'\n')
    code=['// Generated by forged_equipment.py','namespace Delve { public static class ForgedCatalog { public static string Skill(string name) { switch((name ?? "").ToLowerInvariant()) {']
    code+=['case '+json.dumps(r['name'].lower())+':return '+json.dumps(r['skill'])+';' for r in manifest['recipes']]
    code+=['default:return null; } } } }'];(ROOT/'src/Code/ForgedCatalog.generated.cs').write_text('\n'.join(code)+'\n')
