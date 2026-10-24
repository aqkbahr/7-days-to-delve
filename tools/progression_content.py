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
 bind(skill,name,fx('StaminaLoss',-.10,tag))
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
# Special bindings are implemented by ProgressionRuntime rather than XML.
CUSTOM={('PackMule',n) for n in ['Balanced Load','Weight Distribution','Master Packing','Settled Weight','Well Stocked','Ready Reserves','Deep Stores']}
CUSTOM|={('Athletics',n) for n in ['Efficient Motion','Distance Runner','Steady Recovery','Efficient Stroke']}
CUSTOM|={('PackMule',n) for n in ['Trail Supplies','Measured Pace']}
CUSTOM|={(s,n) for s,n in [('Cooking','Kitchen Practice'),('Smithing','Forge Practice'),('Carpentry','Workshop Practice'),('Alchemy','Laboratory Practice'),('Alchemy','Measured Treatment')]}
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
 lines=['// Generated by progression_content.py; do not hand edit.','using System.Collections.Generic;','namespace Delve { public static class TalentCatalog {','public static readonly Dictionary<string,TalentDefinition> Entries = new Dictionary<string,TalentDefinition> {']
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
