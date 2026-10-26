"""Native effect bindings. Anything without a verified binding is unpurchasable.
These bindings are deliberately explicit; numbers are not parsed from prose.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# skill, perk name -> (native passive, value, operation, tags)
BINDINGS={}
def bind(skill,name,*effects): BINDINGS[(skill,name)]=effects
def fx(stat,value,tags='',op='perc_add'):return (stat,value,op,tags)
for skill,name,tag in [('Blades','Blade Familiarity','bladeSkill'),('Blunt','Heavy Grip','clubSkill,sledgeSkill,axe'),('Polearms','Polearm Familiarity','spearSkill'),('Unarmed','Conditioned Hands','knuckleSkill')]:
 # The melee stamina call supplies primary/secondary action tags, not weapon
 # tags. FirstTierWeaponCosts scopes these reductions by the actual ItemValue.
 bind(skill,name)
bind('Blades','Quick Hands',fx('AttacksPerMinute',.10,'bladeSkill'))
bind('Archery',"Archer's Handling",fx('ProjectileVelocity',.10,'bowSkill,archery'))
bind('Archery','Careful Handling',fx('DegradationPerUse',-.15,'bowSkill,archery'))
bind('PackMule','Pack Frames',fx('CarryCapacity',3,op='base_add'))
bind('PackMule','Extra Pouches',fx('CarryCapacity',3,op='base_add'))
bind('PackMule','Reinforced Harness',fx('CarryCapacity',4,op='base_add'))
bind('PackMule','Master Packing',fx('CarryCapacity',4,op='base_add'))
bind('Athletics','Conditioning',fx('StaminaMax',15,op='base_add'))
bind('Athletics','Long Stride',fx('WalkSpeed',.05),fx('RunSpeed',.05))
bind('Athletics','Sure Landing',fx('FallDamageReduction',.25,op='base_add'))
bind('Athletics','Controlled Breathing',fx('BreathHoldDuration',.30))
bind('Stealth','Patient Approach',fx('CrouchSpeed',.10))
bind('Stealth','Low Profile',fx('CrouchSpeed',.15))
for skill,first,second in [('Wands','Wand Familiarity','Steady Focus'),('Staffs','Staff Familiarity','Reinforced Conduit')]:
 bind(skill,first,fx('ReloadSpeedMultiplier',.10,'delve'+skill))
 bind(skill,second,fx('DegradationPerUse',-.15,'delve'+skill))
bind('Totems','Ritual Familiarity',fx('ReloadSpeedMultiplier',.10,'delveTotems'))
bind('HeavyArmor','Durable Metalwork',fx('DegradationPerUse',-.20,'heavyArmorDeg'))
bind('MediumArmor','Layered Hides',fx('DegradationPerUse',-.20,'mediumArmorDeg'))
# Special bindings are implemented by ProgressionRuntime rather than XML.
CUSTOM={('PackMule',n) for n in ['Balanced Load','Weight Distribution','Master Packing','Settled Weight','Well Stocked','Ready Reserves','Deep Stores']}
CUSTOM|={('Athletics',n) for n in ['Efficient Motion','Distance Runner','Steady Recovery','Efficient Stroke']}
CUSTOM|={('PackMule',n) for n in ['Trail Supplies','Measured Pace']}
CUSTOM|={(s,n) for s,n in [('Cooking','Kitchen Practice'),('Smithing','Forge Practice'),('Carpentry','Workshop Practice'),('Alchemy','Laboratory Practice'),('Alchemy','Measured Treatment')]}
CUSTOM|={(s,n) for s,n in [('Blades','Drawing Blood'),('Blunt','Crushing Impact'),('Polearms','Crippling Thrust'),('Unarmed','Combination'),('Totems','Spirit Attunement'),('HeavyArmor','Fitted Plate'),('MediumArmor','Supple Fit'),('LightArmor','Unburdened Fit'),('LightArmor','Quiet Weave'),('Stealth','Soft Steps'),('Farming','Working Hands'),('Farming','Careful Harvest'),('Cooking','Nourishing Recipes'),('Mining','Pick Handling'),('Mining','Sound Technique'),('Smithing','Sound Metalwork'),('Carpentry','Woodwise')]}
# These entries have concrete handlers in Rank20*.cs. Keep the list explicit:
# a newly drafted rank-20 entry must never become purchasable by rank alone.
RANK20 = {
 'Blades':['Powerful Cuts','Exploit Opening'],
 'Blunt':['Breaker','Brawler','Brace'],
 'Polearms':['Point Control','Set Your Feet','Clear Space'],
 'Unarmed':['Quick Jabs','Fleet Foot','Pressure Points'],
 'Archery':['Quick Draw','Practiced Loading','Anatomist'],
 'Wands':['Measured Bolt','Agile Focus','Swift Casting'],
 'Staffs':['Overload','Focused Impact','Shock Front'],
 'Totems':['Mending Current','Lasting Wards','Lingering Malice'],
 'HeavyArmor':['Reinforced Plating','March of Iron','Deep Reserves'],
 'MediumArmor':['Easy Stride','Ready Footwork','Reinforced Seams'],
 'LightArmor':['Fleet Step','Woven Ward','Open Channels'],
 'Stealth':['Light Tread','Shadowcraft','Opening Strike'],
 'Athletics':['Strong Stroke'],
 'Farming':['Green Thumb',"Gatherer's Eye",'Clean Butchery'],
 'Cooking':['Hearty Portions','Trail Rations','Lasting Meals'],
 'Mining':['Stonebreaker','Ore Sense','Sorting Table'],
 'Smithing':['Honed Edge','Reinforced Plates','Efficient Smelting'],
 'Carpentry':['Bowyer','Efficient Framing','Tanner and Weaver'],
 'Alchemy':['Clean Dressings','Potent Brews','Clean Extraction'],
 'PackMule':['Heavy Momentum'],
}
CUSTOM |= {(skill,name) for skill,names in RANK20.items() for name in names}

def enrich(trees):
 for t in trees:
  for p in t['perks']:
   key=(t['skill'],p['name'])
   p['effects']=list(BINDINGS.get(key,()))
   p['implemented']=key in BINDINGS or key in CUSTOM
 return trees

def emit(progress, skills, perks, buffs, node,effect,loc):
 trees=enrich(json.loads((ROOT/'src/Progression/trees.json').read_text(encoding='utf-8')))
 # Keep legacy definitions for save loading; the purchase hook blocks new legacy buys.
 parents={'Blades':'Strength','Blunt':'Strength','Polearms':'Strength','Unarmed':'Strength','Archery':'Dexterity','Wands':'Intelligence','Staffs':'Intelligence','Totems':'Wisdom','HeavyArmor':'Constitution','MediumArmor':'Constitution','LightArmor':'Constitution','PackMule':'Strength','Stealth':'Dexterity','Athletics':'Constitution','Farming':'Wisdom','Cooking':'Wisdom','Mining':'Strength','Smithing':'Strength','Carpentry':'Intelligence','Alchemy':'Intelligence'}
 for t in trees:
  skill=t['skill'];group='delveTree'+skill
  node(skills,'skill',name=group,parent='delveAtt'+parents[skill],name_key=loc(group,skill+' — 15 points'),icon='ui_game_symbol_hammer')
  for p in t['perks']:
   key=p['id'];desc=p['description']
   if not p['implemented']:desc='NOT YET PLAYABLE — purchase disabled. Planned effect: '+desc
   desc+=' Requires proficiency '+str(p['rank'])+'. Costs 1 talent point.'
   if p['rank']==100:desc+=' All 14 ordinary perks and the mastery trial required; choose only one mastery.'
   el=node(perks,'perk',name=key,parent=group,name_key=loc(key,p['name']),desc_key=loc(key+'Desc',desc),icon='ui_game_symbol_hammer',max_level=1,override_cost='1')
   req=node(el,'level_requirements',level=1)
   node(req,'requirement',name='CVarCompare',cvar='delveLevel'+skill,operation='GTE',value=p['rank'],desc_key=loc(key+'Rank','Requires '+skill+' proficiency '+str(p['rank'])))
   for prior in p['prerequisites']:node(req,'requirement',name='ProgressionLevel',progression_name=prior,operation='GTE',value=1,desc_key=loc(key+prior+'Req','Requires '+prior.replace('delvePerk'+skill,'')))
   if not p['implemented']:node(req,'requirement',name='CVarCompare',cvar='delveNeverUnlock',operation='Equals',value=-999,desc_key=loc(key+'Pending','Not yet playable: behavior implementation pending.'))
   eg=node(el,'effect_group')
   for stat,value,op,tags in p['effects']:
    e=effect(eg,stat,value,op,level=1)
    if tags:e.set('tags',tags)
   node(eg,'effect_description',level=1,desc_key=key,long_desc_key=key+'Desc')
 # Dynamic inventory effects are per-player CVars, never universal changes.
 b=node(buffs,'buff',name='delveLoadEffects',name_key=loc('delveLoadEffects','Packed Load'),description_key=loc('delveLoadEffectsDesc','Equivalent full-stack percentage in your backpack. Supplied 25%, Loaded 50%, Packed 75%. Splitting stacks does not increase load.'),icon='ui_game_symbol_pack_mule',remove_on_death='false')
 node(b,'stack_type',value='ignore');node(b,'duration',value=0);node(b,'display_value',value='delvePackedPercent')
 eg=node(b,'effect_group')
 for stat,cvar,op,tags in [('Mobility','delveEncumbranceRelief','perc_add',''),('PhysicalDamageResist','delveLoadArmor','base_add',''),('ReloadSpeedMultiplier','delveLoadReload','perc_add','bowSkill,archery,delveMagic'),('WalkSpeed','delveLoadSpeed','perc_add',''),('RunSpeed','delveLoadSpeed','perc_add',''),('FoodLoss','delveLoadNeeds','perc_add',''),('WaterLoss','delveLoadNeeds','perc_add','')]:
  e=effect(eg,stat,'@'+cvar,op)
  if tags:e.set('tags',tags)
 # C# registry shares the exact names/gates with the generated UI.
 for name,title,desc,duration in [('delveBladeWound','Bleeding','A blade wound causes damage over six seconds.',7),('delveCombo','Combination','Alternate light and heavy unarmed hits. At three, your next heavy hit is a finisher.',0),('delveTotemDecay','Withering','A totem hex deals damage over five seconds.',6)]:
  b=node(buffs,'buff',name=name,name_key=loc(name,title),description_key=loc(name+'Desc',desc),icon='ui_game_symbol_critical',remove_on_death='true')
  node(b,'stack_type',value='replace');node(b,'duration',value=duration)
  if name=='delveCombo':node(b,'display_value',value='delveComboCount')
  if name=='delveBladeWound':
   node(b,'damage_type',value='bloodloss');node(b,'damage_source',value='Internal')
   eg=node(b,'effect_group')
   node(eg,'triggered_effect',trigger='onSelfBuffStart',action='AttachParticleEffectToEntity',particle='p_bleeding',parent_transform='.body',local_offset='0,0,0')
   for trigger in ['onSelfBuffRemove','onSelfDied']:node(eg,'triggered_effect',trigger=trigger,action='RemoveParticleEffectFromEntity',particle='p_bleeding')
 lines=['// Generated by progression_content.py; do not hand edit.','using System.Collections.Generic;','namespace Delve { public static class TalentCatalog {','static TalentCatalog(){SummonTalents.Register(Entries);}','public static readonly Dictionary<string,TalentDefinition> Entries = new Dictionary<string,TalentDefinition>(System.StringComparer.OrdinalIgnoreCase) {']
 for t in trees:
  for p in t['perks']:
   q=json.dumps
   lines.append('{'+q(p['id'])+',new TalentDefinition('+q(t['skill'])+','+str(p['rank'])+','+str(p['implemented']).lower()+',new string[]{'+','.join(q(x) for x in p['prerequisites'])+'})},')
 lines+=['}; }}']
 (ROOT/'src/Code/TalentCatalog.generated.cs').write_text('\n'.join(lines),encoding='utf-8')
 (ROOT/'artifacts/validation').mkdir(exist_ok=True,parents=True)
 enabled=[p['id'] for t in trees for p in t['perks'] if p['implemented']]
 (ROOT/'artifacts/validation/progression-coverage.json').write_text(json.dumps({'trees':len(trees),'ordinary_perks':280,'total_choices':sum(len(t['perks']) for t in trees),'implemented':enabled,'pending':[p['id'] for t in trees for p in t['perks'] if not p['implemented']]},indent=2),encoding='utf-8')
 print('Progression bindings:',len(enabled),'implemented;',sum(len(t['perks']) for t in trees)-len(enabled),'locked pending behavior.')
