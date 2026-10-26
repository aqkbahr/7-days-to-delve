from pathlib import Path
import shutil,json,os,uuid
from lxml import etree as E
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-08';M=R/'src/ZZZZZZZZZZZZZDelveBatch08';P=R/'playtest/BatchEight'
A.mkdir(exist_ok=True);B=R/'dist/Delve-Batch05-Complete-20261026-110400';assert B.is_dir();(A/'base.txt').write_text(str(B))
for d in ['Config/XUi_Menu','Resources','Textures','UIAtlases/ItemIconAtlas']:(M/d).mkdir(parents=True,exist_ok=True)
(M/'ModInfo.xml').write_text('<xml><Name value="DelveBatch08"/><DisplayName value="Delve Batch 8 - Wayrest and Character"/><Version value="0.14.0"/><Author value="Delve"/></xml>')
shutil.copy2('C:/Users/Michael/.codex/generated_images/01a16ed9-6290-7943-9a9f-dbcceaba0724/exec-23d59b2e-f0ab-4a4c-8812-90c1734c82ed.png',M/'Textures/delve-logo.png')
root=E.Element('configs');E.SubElement(root,'set',xpath="/windows/window[@name='mainMenu']/texture[@name='gameLogo']/@texture").text='@modfolder:Textures/delve-logo.png'
E.ElementTree(root).write(str(M/'Config/XUi_Menu/windows.xml'),encoding='utf-8',pretty_print=True)
root=E.Element('configs');E.SubElement(root,'set',xpath="/blocks/block[@name='delveFieldCraftingMat']/property[@name='Model']/@value").text='#@modfolder:Resources/fieldmatbatch08.unity3d?delveFieldCraftingMat'
E.ElementTree(root).write(str(M/'Config/blocks.xml'),encoding='utf-8',pretty_print=True)
art=A/'art/UnityProject'
for d in ['Assets/Editor','Packages','ProjectSettings']:(art/d).mkdir(parents=True,exist_ok=True)
for n in ['Packages/manifest.json','ProjectSettings/ProjectVersion.txt']:shutil.copy2(R/'artifacts/batch-05/art/UnityProject'/n,art/n)
s=(R/'tools/art/BuildFieldMat.cs').read_text().replace('BuildFieldMat','BuildBatchEightMat').replace('fieldmat.unity3d','fieldmatbatch08.unity3d')
s=s.replace('m.color=color;m.SetFloat', '''var tex=new Texture2D(64,64,TextureFormat.RGBA32,false);for(int y=0;y<64;y++)for(int x=0;x<64;x++){float tone=.83f+.2f*Mathf.PerlinNoise(x*.5f,y*.06f);tex.SetPixel(x,y,new Color(color.r*tone,color.g*tone,color.b*tone,1));}tex.Apply();AssetDatabase.CreateAsset(tex,"Assets/Generated/"+name+"Albedo.asset");m.mainTexture=tex;m.color=Color.white;m.SetFloat''')
(R/'tools/art/BuildBatchEightMat.cs').write_text(s);(art/'Assets/Editor/BuildBatchEightMat.cs').write_text(s)
# Fixed, auditable furnishing placements; never touch the central square/fire.
rows=[]
def place(room,x,y,z,block,rotation=0):rows.append(dict(room=room,x=x,y=y,z=z,block=block,rotation=rotation))
for room,x,z,n in [('smithy',9,32,'delveForgeAnvil'),('smithy',15,32,'delveSortingTable'),('carpenter',9,12,'delveSawKit'),('carpenter',16,14,'delveOutfittingKit'),('carpenter',13,14,'delveFieldCraftingMat'),('pantry',45,32,'delveFarmDispatch'),('pantry',49,32,'delveGrainMill'),('pantry',45,35,'delveFieldHearth'),('temple',45,14,'delveMortarKit'),('temple',51,14,'delveInscriptionKit')]:place(room,x,2,z,n)
for room,x,z in [('smithy',9,40),('pantry',50,40)]:place(room,x,2,z,'bedroll')
for room,x,z in [('smithy',14,40),('carpenter',18,18),('pantry',46,40)]:place(room,x,2,z,'cntWoodenChestClosed')
for room,x,z in [('smithy',11,36),('carpenter',18,15),('pantry',51,35)]:
 place(room,x,2,z,'woodShapes:cube');place(room,x,3,z,'candleTableLight')
# Town meeting tables with a clear middle aisle and a route to the steward.
for x in [24,25,26,34,35,36]:place('townhall',x,2,43,'woodShapes:cube')
for x in [24,26,34,36]:
 place('townhall',x,2,42,'chairWood01')
for x in [24,36]:place('townhall',x,3,43,'candleTableLight')
for x in [23,38]:place('townhall',x,2,50,'cntBookcaseFull')
for x in [46,50]:
 place('temple',x,3,18,'candleTableLight')
 for z in [13,15]:place('temple',x,2,z,'woodShapes:cubeHalf')
for x in [46,50]:place('temple',x,2,20,'cntBookcaseFull')
doc=E.Element('furnishings')
for r in rows:E.SubElement(doc,'cell',**{k:str(v) for k,v in r.items()})
E.ElementTree(doc).write(str(A/'furnishings.xml'),encoding='utf-8',pretty_print=True)
assert not P.exists(),'Existing fixture; do not overwrite'
P.mkdir()
for e in json.loads((B/'manifest.json').read_text())['files']:
 n=e['path']
 if not n.startswith(('Mods/','Worlds/')):continue
 target=P/n.replace('Worlds/','GeneratedWorlds/',1);target.parent.mkdir(parents=True,exist_ok=True)
 # Everything copied: native prefab serializer must never edit a hardlinked release.
 shutil.copy2(B/n,target)
shutil.copytree(M,P/'Mods'/M.name)
shutil.copytree(R/'playtest/BatchFiveComplete/Mods/StationProbe',P/'Mods/StationProbe')
shutil.copy2(A/'furnishings.xml',P/'Mods/StationProbe/furnishings.xml')
cfg=E.parse(str(R/'playtest/BatchFiveComplete/serverconfig.xml'))
for n,v in {'GameName':'BatchEight','UserDataFolder':str(P),'ServerName':'Batch Eight Verification','ServerPort':'29410','TelnetPort':'29419','TelnetPassword':uuid.uuid4().hex}.items():cfg.find(f"property[@name='{n}']").set('value',v)
cfg.write(str(P/'serverconfig.xml'),encoding='utf-8',xml_declaration=True)
(P/'profile.json').write_text(json.dumps({'GamePath':'D:/Steam/steamapps/common/7 Days To Die','ProfilePath':str(P)}))
print('Prepared D: Batch Eight fixture, furnishing plan and textured-mat authoring project')
