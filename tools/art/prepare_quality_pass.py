"""Create an isolated art workspace; never mutate the active playtest or source models."""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[2]
STAGE=Path('D:/AlliumArt/QualityPass20261025')
groups={'weapons':'forest-weapons','props':'forest-props','armor':'forest-armor','enemies':'forest-enemies','quadrupeds':'forest-quadrupeds','thornback':'thornback','batchone':'batch-01/art','batchthree':'batch-03/art','batchfour':'batch-04/art'}
models=[]
def add(group,asset,blend,fbx,texture,slot):
    ident=asset.get('id',asset.get('entity'))
    models.append(dict(id=ident,group=group,kind=asset.get('kind',asset.get('family','creature')),slot=slot,blend=str(blend),fbx=fbx,texture=texture,animations=asset.get('animations',{}),native_footprint=asset.get('native_footprint'),set=asset.get('set'),bundle=ident.lower()+'.unity3d' if group in ('enemies','quadrupeds') else 'thornback.unity3d' if group=='thornback' else 'forest'+group+'.unity3d'))
for group,folder,key,slot in [('weapons','ForestWeapons','weapons','Weapon'),('props','ForestProps','assets','Prop'),('armor','ForestArmor','armor',None),('enemies','ForestEnemies','enemies','Creature')]:
    source=ROOT/'src/Art'/folder;cat=json.loads((source/'catalogue.json').read_text())
    for a in cat[key]:
        ident=a.get('id',a.get('entity'));s=a.get('slot',slot)
        if group=='armor':blend=source/(a['set']+'.blend')
        else:blend=source/ident/(ident+'.blend')
        fbx=('Creatures/'+ident+'/' if group=='enemies' else 'Models/')+ident+'.fbx'
        texture='Creatures/'+ident+'/Albedo.png' if group=='enemies' else 'Forest'+('Weapon' if group=='weapons' else 'Prop' if group=='props' else 'Armor')+'Atlas.png'
        add(group,a,blend,fbx,texture,s)
for ident in ('delveHellhound','delveGloomcat','delveCrystalStag','delveThornbackBoar'):
    folder=ROOT/'src/Art'/ident;a=json.loads((folder/'asset-manifest.json').read_text());a['id']=ident
    thorn=ident=='delveThornbackBoar';group='thornback' if thorn else 'quadrupeds'
    add(group,a,folder/(ident+'.blend'),('Thornback/' if thorn else 'Creatures/'+ident+'/')+ident+'.fbx','Thornback/Thornback_Albedo.png' if thorn else 'Creatures/'+ident+'/Albedo.png','Thornback' if thorn else 'Creature')
for group,folder in groups.items():
    source=ROOT/'artifacts'/folder/'UnityProject/Assets';dest=STAGE/'UnityProject/Assets/Legacy'/group
    if not source.exists():continue
    def ignore(path,names):return [n for n in names if n=='Editor' or n.endswith('.cs') or n.endswith('.cs.meta')]
    if not dest.exists():shutil.copytree(source,dest,ignore=ignore)
    if group.startswith('batch'):
        for p in sorted((dest/'Generated').glob('*.prefab')):models.append(dict(id=p.stem,group=group,kind='prop',slot='',blend='',fbx='',texture='',animations={},bundle=group+'.unity3d'))
for m in models:
    if m['blend'] and not Path(m['blend']).exists():raise FileNotFoundError(m['blend'])
    m['prefab']='Assets/Legacy/'+m['group']+'/Generated/'+m['id']+'.prefab'
    if m['group']=='thornback':
        print('Thornback prefabs',list((STAGE/'UnityProject/Assets/Legacy/thornback/Generated').glob('*.prefab')))
    m['destination']=str(STAGE/'Sources'/m['group']/m['id'])
(STAGE/'inventory.json').write_text(json.dumps({'models':models,'groups':groups},indent=2))
print('STAGED',len(models),'models',len(groups),'groups',STAGE)
