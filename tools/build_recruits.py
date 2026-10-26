"""Author the isolated Wayrest recruitment content module."""
from pathlib import Path
import csv
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'src/ZDelveRecruits'
C=MOD/'Config'
C.mkdir(parents=True,exist_ok=True)
def save(path,root):
    E.indent(root);E.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
def patch(file,xpath):
    r=E.Element('configs');a=E.SubElement(r,'append',xpath=xpath);return r,a
def prop(parent,name,value):E.SubElement(parent,'property',name=name,value=str(value))
save(MOD/'ModInfo.xml',E.fromstring('<xml><Name value="ZDelveRecruits"/><DisplayName value="Delve - Wayrest Recruits"/><Version value="0.2.0"/><Description value="Settlement recruitment and shrine resurrection"/><Author value="Delve"/></xml>'))
r,a=patch('blocks','/blocks')
for name,base,cls in [('delveRecruitLedger','cntWoodWritableCrate','Delve.BlockDelveRecruitLedger, Delve'),('delveRallyFlag','woodLogPillar100','Delve.BlockDelveRallyFlag, Delve'),('delveRecoveryShrine','graveStone01','Delve.BlockDelveRecoveryShrine, Delve')]:
    b=E.SubElement(a,'block',name=name)
    for k,v in [('Extends',base),('Class',cls),('DescriptionKey',name+'Desc'),('CreativeMode','Player'),('CustomIcon',base)]:prop(b,k,v)
    if name=='delveRecoveryShrine':
        prop(b,'IsTerrainDecoration','false');prop(b,'MaxDamage','500')
save(C/'blocks.xml',r)
r,a=patch('recipes','/recipes')
for name,wood,cloth in [('delveRecruitLedger',20,0),('delveRallyFlag',15,5)]:
    q=E.SubElement(a,'recipe',name=name,count='1',craft_time='10')
    E.SubElement(q,'ingredient',name='resourceWood',count=str(wood))
    if cloth:E.SubElement(q,'ingredient',name='resourceCloth',count=str(cloth))
q=E.SubElement(a,'recipe',name='delveRecoveryShrine',count='1',craft_time='20')
for item,count in [('resourceRockSmall',30),('resourceWood',10),('resourceCloth',5)]:E.SubElement(q,'ingredient',name=item,count=str(count))
save(C/'recipes.xml',r)
r,a=patch('items','/items')
for role,damage in [('Worker',8),('Defender',20)]:
    item=E.SubElement(a,'item',name='meleeHandDelve'+role)
    prop(item,'Extends','meleeHandPlayer');prop(item,'CreativeMode','None')
    effect=E.SubElement(item,'effect_group',name='Recruit melee',tiered='false')
    E.SubElement(effect,'passive_effect',name='EntityDamage',operation='base_set',value=str(damage))
    E.SubElement(effect,'passive_effect',name='BlockDamage',operation='base_set',value='0')
save(C/'items.xml',r)
r,a=patch('entities','/entity_classes')
for role,hp,base in [('Worker',120,'npcTraderBob'),('Defender',240,'npcTraderHugh')]:
    entity=E.SubElement(a,'entity_class',name='delveRecruit'+role,extends=base)
    for k,v in [('Class','Delve.EntityDelveRecruit, Delve'),('Tags','entity,npc,human'),('NPCID','delveRecruit'+role),('UserSpawnType','None'),('Faction','whiteriver'),('IsEnemyEntity','false'),('NavObject',''),('HandItem','meleeHandDelve'+role),('LootList',''),('ExperienceGain','0'),('AITask-1','ApproachAndAttackTarget'),('AITarget-1',''),('MoveSpeed','0.75')]:prop(entity,k,v)
    entity.find("property[@name='AITask-1']").set('data','class=EntityZombie,0,EntityEnemyAnimal,0')
    effect=E.SubElement(entity,'effect_group',name='Recruit health')
    E.SubElement(effect,'passive_effect',name='HealthMax',operation='base_set',value=str(hp))
save(C/'entityclasses.xml',r)
r,a=patch('npc','/npc')
for role in ['Worker','Defender']:
    E.SubElement(a,'npc_info',id='delveRecruit'+role,name='Wayrest '+role,name_key='delveRecruit'+role,faction='whiteriver',portrait='npc_joel',greeting_type='none',stance='Like',voice_set='',dialog_id='delveWayrest')
save(C/'npc.xml',r)
r,a=patch('dialogs',"/dialogs/dialog[@id='delveWayrest']/statement[@id='start']")
E.SubElement(a,'response_entry',id='wayrestRecruitment')
a=E.SubElement(r,'append',xpath="/dialogs/dialog[@id='delveWayrest']")
E.SubElement(a,'response',id='wayrestRecruitment',text='delveAskRecruits',nextstatementid='wayrestRecruitment')
s=E.SubElement(a,'statement',id='wayrestRecruitment',text='delveRecruitWelcome')
for key in ['wayrestOpenRoster','wayrestResurrection','nevermind']:E.SubElement(s,'response_entry',id=key)
E.SubElement(a,'response',id='wayrestResurrection',text='delveAskResurrection',nextstatementid='wayrestResurrection')
s=E.SubElement(a,'statement',id='wayrestResurrection',text='delveResurrectionWelcome')
for key in ['wayrestOpenRoster','nevermind']:E.SubElement(s,'response_entry',id=key)
response=E.SubElement(a,'response',id='wayrestOpenRoster',text='delveOpenRoster')
E.SubElement(response,'action',type='Delve.DialogActionDelveRecruits, Delve',id='open')
save(C/'dialogs.xml',r)
ui=C/'XUi_InGame';ui.mkdir(exist_ok=True)
r,a=patch('xui','/xui');g=E.SubElement(a,'window_group',name='delveRecruits');E.SubElement(g,'window',name='delveRecruitWindow');save(ui/'xui.xml',r)
r,a=patch('windows','/windows')
w=E.SubElement(a,'window',name='delveRecruitWindow',anchor='Center',pos='-550,350',width='1100',height='700',controller='Delve.XUiC_RecruitScreen, Delve',cursor_area='true')
E.SubElement(w,'sprite',name='background',width='1100',height='700',sprite='menu_empty',color='17,25,33,250',depth='1',type='sliced')
def label(name,x,y,width,height,text,size=19):E.SubElement(w,'label',name=name,pos=f'{x},{-y}',width=str(width),height=str(height),text=text,font_size=str(size),depth='5',color='230,225,210',justify='left',pivot='topleft')
def button(name,x,y,width,text):E.SubElement(w,'simplebutton',name=name,pos=f'{x},{-y}',width=str(width),height='36',caption=text,font_size='18',depth='4',defaultcolor='38,49,60',hovercolor='67,84,96')
label('title',20,15,900,40,'WAYREST / SETTLEMENT RECRUITS',28);button('nr_close',1030,15,50,'X')
button('nr_settlement',20,65,690,'{nr_settlement}');button('nr_refresh',730,65,160,'Refresh')
label('intro',20,110,1060,65,'Deposit gold in your Settlement Ledger and close its storage before hiring.\nTier 1: Smith 400 gold | Cook 250 gold | Defender 500 gold. Hiring creates a reserve recruit.')
button('nr_hireSmith',20,175,210,'Hire smith / 400');button('nr_hireCook',240,175,210,'Hire cook / 250');button('nr_hireDefender',460,175,250,'Hire defender / 500')
button('nr_resurrect',730,175,340,'Resurrect / 1 game hour')
w.find("simplebutton[@name='nr_resurrect']").set('visible','{nr_atshrine}')
label('page',20,225,420,30,'{nr_page}')
for i in range(8):button('nr_row'+str(i),20,260+i*40,410,'{nr_row'+str(i)+'}')
label('detail',460,225,610,355,'{nr_detail}',18)
button('nr_prev',20,590,195,'Previous');button('nr_next',235,590,195,'Next')
button('nr_assign',460,590,280,'Assign here');button('nr_recall',755,590,315,'Recall to reserve')
label('message',20,640,1060,55,'{nr_message}',18)
save(ui/'windows.xml',r)
strings={
 'delveRecruitLedger':'Settlement Ledger',
 'delveRecruitLedgerDesc':'Place inside your active Settlement Stone. Open storage to deposit gold, then close it. Hold Interact and choose Manage recruits to register this settlement and hire smiths, cooks and defenders. One ledger treasury per Stone; using another ledger moves the treasury link. Recruits belong to the settlement and current allied party members can help manage them.',
 'delveRallyFlag':'Recruit Rally Flag',
 'delveRallyFlagDesc':'A timber rally post for your defenders. Place inside an active Settlement Stone with clear standing space alongside it. Interact to assign one recruit. Guards engage undead within six meters and stay within eight meters of the post. Workers may guard too, but are weaker than defenders.',
 'delveAskRecruits':'I want to hire workers and defenders.',
 'delveOpenRoster':'Open the settlement roster.',
 'delveRecruitWelcome':'A settlement needs more than walls. Our smiths and cooks will work your stations, and defenders will hold a rally point. Craft a Settlement Ledger, place it inside your active Settlement Stone, and use Manage recruits to register it. Deposit gold in its storage and close the container before hiring. Smiths cost 400, cooks 250, defenders 500. Select a recruit in the roster, then hold Interact on a forge, hearth or rally flag and choose Manage recruits to assign them. One recruit per station; you may hire more than one of each role. They belong to the settlement. Recall keeps them in reserve. Ask me about the Shrine of Return if someone falls.',
 'delveRecoveryShrine':'Shrine of Return',
 'delveRecoveryShrineDesc':'A stone memorial where fallen recruits can return. Place inside an active Settlement Stone registered through a Settlement Ledger. Interact, select a fallen recruit, then choose Resurrect. One ritual per shrine takes one in-game hour, with no priest or consumable payment. The same recruit returns to reserve at full health with their name, role and tier unchanged. A lost shrine or claim interrupts the ritual but never deletes the fallen record.',
 'delveAskResurrection':'Can we bring our fallen recruits back?',
 'delveResurrectionWelcome':'A fallen companion is not forgotten. Their record remains with the settlement, and I can help you find it in the roster. Craft a Shrine of Return with 30 stone, 10 wood and 5 cloth. Place it within a registered active Settlement Stone, approach it, and select the fallen recruit. The ritual takes one hour of the world\'s time. You need no priest and no offering for this rite. They return to reserve at full health, keeping their identity, role and tier. Assign them again when you are ready. If a shrine or Stone is lost, their record stays safe. Use another active Stone belonging to the same owner and begin again.',
 'delveRecruitWorker':'Wayrest Worker', 'delveRecruitDefender':'Wayrest Defender',
}
with (C/'Localization.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.writer(f);writer.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english'])
    for k,v in strings.items():writer.writerow([k,'ZDelveRecruits','','','',v])
print('Authored Wayrest recruitment module')
