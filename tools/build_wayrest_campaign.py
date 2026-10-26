"""Author Wayrest contracts using native objective implementations and selection."""
from pathlib import Path
import copy,csv,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/'src/DelveWayrest/Config'
native=E.parse('D:/Steam/steamapps/common/7 Days To Die/Data/Config/quests.xml').getroot()
def save(path,root):
    E.indent(root);E.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
def prop(q,k,v):
    e=q.find(f"property[@name='{k}']")
    if e is None:e=E.SubElement(q,'property',name=k)
    e.set('value',str(v));e.attrib.pop('param1',None)
root=E.Element('configs');a=E.SubElement(root,'append',xpath='/quests')
a.append(copy.deepcopy(E.parse(C/'quests.xml').find(".//quest[@id='delveWayrestSupplies']")))
strings={}
for suffix,base,title in [('Fetch','tier1_fetch','Recover Woodland Supplies'),('Clear','tier1_clear','Clear the Woodland Ruins'),('FetchClear','tier2_fetch_clear','Secure and Recover')]:
    q=copy.deepcopy(native.find(f"quest[@id='{base}']"));q.set('id','delveWayrest'+suffix)
    prop(q,'name_key',q.get('id'));strings[q.get('id')]='Wayrest: '+title
    prop(q,'difficulty_tier',1);prop(q,'add_to_tier_complete','false')
    prop(q,'reward_choices_count',3)
    for e in q.findall('.//property'):
        e.attrib.pop('param1',None)
        if e.get('name')=='biome_filter_type':e.set('value','OnlyBiome')
        if e.get('name')=='biome_filter':e.set('value','pine_forest')
    # Retain native rally, fetch, sleeper, return, and party behavior.
    for r in list(q.findall('reward')):q.remove(r)
    E.SubElement(q,'reward',type='Exp',value='2500' if suffix!='FetchClear' else '3000')
    E.SubElement(q,'reward',type='Item',id='casinoCoin',value='150' if suffix!='FetchClear' else '200')
    for item,count in [('delveHealingPoultice',3),('foodCornBread',3),('resourceForgedIron',8)]:
        E.SubElement(q,'reward',type='Item',id=item,value=str(count),ischosen='true')
    a.append(q)
q=E.SubElement(a,'quest',id='delveWayrestReclamation')
for k,v in dict(name_key='delveWayrestReclamation',description_key='delveWayrestReclamationDesc',offer_key='delveWayrestReclamationDesc',subtitle_key='delveWayrestReclamationSub',icon='ui_game_symbol_quest',category_key='quest',repeatable='false',shareable='false',add_to_tier_complete='false',completiontype='AutoComplete').items():prop(q,k,v)
E.SubElement(q,'objective',type='DelveWayrest, Delve',value='10',phase='1')
q=copy.deepcopy(native.find("quest[@id='tier2_nexttrader']"));q.set('id','delveWayrestOnward')
for k,v in dict(name_key='delveWayrestOnward',description_key='delveWayrestOnwardDesc',offer_key='delveWayrestOnwardDesc',difficulty_tier='1',unique_key='delveWayrestOnward',quest_hint_requirement='',reward_choices_count='1').items():prop(q,k,v)
for e in q.findall('.//property'):e.attrib.pop('param1',None)
for r in list(q.findall('reward')):q.remove(r)
E.SubElement(q,'reward',type='Exp',value='1000');E.SubElement(q,'reward',type='Item',id='delveWardDraught',value='2')
a.append(q)
pool=E.SubElement(a,'quest_list',id='delveWayrestJobs')
for suffix in ['Fetch','Clear','FetchClear']:E.SubElement(pool,'quest',id='delveWayrest'+suffix)
E.SubElement(pool,'quest',id='delveWayrestOnward',cvar='delveWayrestReady')
save(C/'quests.xml',root)
tree=E.parse(C/'npc.xml');tree.find('.//npc_info').set('quest_list','delveWayrestJobs');save(C/'npc.xml',tree.getroot())
tree=E.parse(C/'dialogs.xml');welcome=tree.find(".//statement[@id='wayrestWelcome']")
if welcome.find("quest_entry[@id='delveWayrestReclamation']") is None:welcome.insert(0,E.Element('quest_entry',id='delveWayrestReclamation',type='add',listindex='0'))
# Only the local Tier 1 board belongs to this steward; onward uses special jobs.
for parent in tree.iter():
    for e in list(parent):
        if e.tag=='response_entry' and (e.get('id','').startswith('jobsnext') or e.get('id') in ['jobshave2','jobshave3','jobshave4','jobshave5','jobshave6']):parent.remove(e)
save(C/'dialogs.xml',tree.getroot())
root=E.fromstring('<configs><append xpath="/buffs"><buff name="delveWayrestProgress" name_key="delveWayrestProgress" description_key="delveWayrestProgressDesc" icon="ui_game_symbol_quest" remove_on_death="false"><stack_type value="ignore"/><duration value="0"/><display_value value="delveWayrestJobs"/></buff></append></configs>');save(C/'buffs.xml',root)
strings.update({
 'delveWayrestReclamation':'Reclaim Wayrest',
 'delveWayrestReclamationSub':'Ten contracts for the Living Border',
 'delveWayrestReclamationDesc':'Complete ten contracts from the Wayrest Steward. All adventurers contribute to the same world tally. A shared contract counts once when its owner turns it in. Failed or abandoned jobs do not count. At 10/10 ask the Steward for the special road-to-Arbor job. Ordinary work remains available afterward.',
 'delveWayrestOnward':'The Road to Arbor Camp',
 'delveWayrestOnwardDesc':'Wayrest has ten completed contracts. Follow the main road to Arbor Camp and speak to its leader. The Burnt Arbor remains hazardous: prepare protection and supplies before entering. Your arrival opens the next chapter for this world.',
 'delveWayrestProgress':'Wayrest contracts completed / 10',
 'delveWayrestProgressDesc':'World-shared reclamation. Any ten Wayrest contracts count; shared jobs count once at the owner\'s hand-in. Check Reclaim Wayrest in the quest journal. At ten, request the special onward job from the Steward.',
 'delveWayrestWelcome':'Wayrest serves the Living Border. The smithy, supplies and shelter surround our hearth. Take the reclamation journal here, then ask for jobs. Ten completed contracts restore our foothold and open the road to Arbor Camp. Recovery and clear jobs rotate across suitable Forest ruins. The supply exercise below is optional preparation and does not count toward the ten.'})
rows=list(csv.reader((C/'Localization.csv').open(encoding='utf-8')))
rows=[r for r in rows if r and r[0] not in strings]
rows.extend([[k,'DelveWayrest','','','','',v] for k,v in strings.items()])
with (C/'Localization.csv').open('w',encoding='utf-8',newline='') as f:csv.writer(f).writerows(rows)
print('Wayrest contract pool, journal, onward quest and localization generated')

# Apply shared first-playthrough story after generation.
from intro_story import apply_wayrest
apply_wayrest()
from forest_onboarding import apply as apply_onboarding
apply_onboarding()
