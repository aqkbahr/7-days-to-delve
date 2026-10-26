"""Review/package and integrate validated reconstructed weapon art into source inputs."""
from pathlib import Path
import json,hashlib,shutil,html,sys,xml.etree.ElementTree as E
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];STAGE=Path('D:/Projects/Codex/7DaysToDelve/WeaponRebuild20261026')
catalogue=json.loads((STAGE/'weapons.json').read_text());specs=catalogue['weapons'];aliases=catalogue['aliases'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
validation=(STAGE/'Reports/unity-validation.txt').read_text();bundle=(STAGE/'Reports/bundle-validation.txt').read_text()
assert validation.startswith('PASS models=37 full=True') and validation.count(' PASS ')==37
assert bundle.startswith('PASS ')
assert 'SHA256='+sha(STAGE/'Delivery/Resources/forestweapons.unity3d') in bundle,'Reload evidence must match the exact delivered bundle'
assets=STAGE/'UnityProject/Assets';icons=STAGE/'Delivery/UIAtlases/ItemIconAtlas'
for source,target in aliases.items():shutil.copy2(icons/(target+'.png'),icons/(source+'.png'))
for p in icons.glob('*.png'):
    im=Image.open(p);assert im.mode=='RGBA' and im.size==(256,256) and im.getchannel('A').getextrema()==(0,255),p
assert len(list(icons.glob('*.png')))==41
fontpath='C:/Windows/Fonts/segoeui.ttf';font=ImageFont.truetype(fontpath,23);small=ImageFont.truetype(fontpath,17)
def sheet(ids,cols,width,height,file):
    rows=(len(ids)+cols-1)//cols;canvas=Image.new('RGB',(cols*width,rows*height),'#0b1014');draw=ImageDraw.Draw(canvas)
    for index,ident in enumerate(ids):
        spec=next(s for s in specs if s['id']==ident);im=Image.open(STAGE/'Review'/ident/'hero.png').convert('RGB');im.thumbnail((width,height-65));x=index%cols*width+(width-im.width)//2;y=index//cols*height;canvas.paste(im,(x,y));draw.text((index%cols*width+12,y+height-58),spec['name'],fill='#e5e0d5',font=small);draw.text((index%cols*width+12,y+height-33),spec['tier'],fill='#b2c1cb',font=small)
    canvas.save(STAGE/'Review'/file,quality=95)
main=[s['id'] for s in specs if s['family'] not in ('rune','arrow','bolt')]
sheet(main,4,350,430,'all-weapons.jpg');sheet([s['id'] for s in specs if s['id'] not in main],4,350,360,'runes-ammunition.jpg')
highlights=['delveForgedDagger','delveForgedMace','delveForgedCrossbow','delveForgedWand','delveForgedTotem','delveForgedMendingTotem']
sheet(highlights,3,430,470,'highlights.jpg')
before=Image.new('RGB',(1024,4*555),'#0b1014');draw=ImageDraw.Draw(before)
for row,ident in enumerate(('delveForgedDagger','delveForgedCrossbow','delveForgedWand','delveForgedTotem')):
    old=ROOT/'artifacts/forest-weapons/QualityReview'/ident/'view-0.png'
    for col,p in enumerate((old,STAGE/'Review'/ident/'hero.png')):
        if p.exists():before.paste(Image.open(p).convert('RGB').resize((512,512)),(col*512,row*555))
    draw.text((12,row*555+520),'Previous — '+ident,fill='white',font=small);draw.text((524,row*555+520),'Rebuilt — '+ident,fill='white',font=small)
before.save(STAGE/'Review/before-after.jpg',quality=94)
for ident in main:
    folder=STAGE/'Review'/ident;frames=[Image.open(p).convert('RGB') for p in sorted(folder.glob('motion-*.png'))];assert len(frames)==8
    frames[0].save(folder/'motion.gif',save_all=True,append_images=frames[1:],duration=130,loop=0)
cards=[]
for spec in specs:
    ident=spec['id'];info=json.loads((STAGE/'Sources'/ident/'model.json').read_text());pics=''.join('<a href="Review/'+ident+'/'+name+'"><img loading="lazy" src="Review/'+ident+'/'+name+'"></a>' for name in ('hero.png','side.png','back.png'));motion='<p><a href="Review/'+ident+'/motion.gif">Animation preview</a></p>' if ident in main else ''
    cards.append('<article data-tier="'+spec['tier']+'"><h2>'+html.escape(spec['name'])+'</h2><p>'+html.escape(spec['tier']+' · '+spec['family'])+' · Blender LOD triangles '+str(info['triangles'])+' · '+str(info['clips'])+' preserved clips</p><div>'+pics+'</div>'+motion+'</article>')
page='''<!doctype html><meta charset="utf-8"><title>Forest weapon reconstruction</title><style>body{background:#0b1014;color:#e5e0d5;font:16px system-ui;margin:30px}h1{font-size:32px}h2{font-size:22px}article{background:#172027;margin:22px 0;padding:18px}article div{display:flex}img{width:100%;max-width:430px}p{max-width:1100px;line-height:1.55}a{color:#9dcad8}.wide{max-width:1500px}</style><h1>Weapons rebuilt — Field and Forged</h1><p>20 weapons and magical focuses, 13 rune models and 4 ammunition variants rebuilt around their existing rig and socket contracts. New shaped blades and fittings, distinct wood and leather surfaces, honed steel edges, bindings and saddle stitches, laminated bows, contoured crossbow stock with rails and trigger furniture, carved totems and faceted crystal settings. Original generated material artwork with five PBR maps; per-part color and geometric occlusion. Three LODs each.</p><img class="wide" src="Review/highlights.jpg"><p><a href="Review/all-weapons.jpg">All weapons</a> · <a href="Review/runes-ammunition.jpg">Runes and ammunition</a> · <a href="Review/before-after.jpg">Previous / rebuilt</a> · <a href="Reports/unity-validation.txt">Unity validation</a> · <a href="Reports/bundle-validation.txt">Exported bundle reload</a> · <a href="Reports/held-corrections.txt">Existing grip-correction checks</a> · <a href="Reports/README.txt">Source and integration report</a> · <a href="Artwork/prompt.txt">Original texture prompt</a></p><p>These are offline Unity renders and prop animation previews. Existing player and enemy animation controllers remain authoritative in game. Before/after review lighting differs. Actual first-person hand clipping, in-game lighting and combat, multiplayer and performance remain to be checked; automated checks do not establish artistic parity with vanilla.</p>'''
(STAGE/'gallery.html').write_text(page+''.join(cards),encoding='utf-8')
if '--integrate' in sys.argv:
    baseline=json.loads((STAGE/'Reports/production-baseline.json').read_text())
    pointer='dist/latest-first-forest-release.txt'
    release_at_start=(ROOT/pointer).read_text().strip()
    for relative,digest in baseline.items():
        if relative!=pointer:assert sha(ROOT/relative)==digest,'Concurrent production change '+relative
    files={};backup_root=STAGE/'SourceBackup'
    def copy(source,target):
        source,target=Path(source),Path(target)
        if target.exists() and source.read_bytes()==target.read_bytes():return
        relative=target.relative_to(ROOT)
        if target.exists():
            backup=backup_root/relative;backup.parent.mkdir(parents=True,exist_ok=True);assert not backup.exists(),'Backup already exists '+str(relative);shutil.copy2(target,backup);files[str(relative)]={'before':sha(target)}
        else:files[str(relative)]={'before':None}
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);files[str(relative)]['after']=sha(target)
    source_art=ROOT/'src/Art/ForestWeapons';project=ROOT/'artifacts/forest-weapons/UnityProject';canonical=json.loads((source_art/'catalogue.json').read_text());lookup={s['id']:s for s in canonical['weapons']}
    canonical['integration']='WeaponRebuild20261026: reconstructed canonical art and bundle ready for the next package; original held runtime and gameplay definitions preserved. Project: '+str(STAGE)
    for spec in specs:
        ident=spec['id'];info=json.loads((STAGE/'Sources'/ident/'model.json').read_text());entry=lookup[ident]
        assert entry['bones']==spec['bones'] and entry['animations']==spec['animations']
        copy(STAGE/'Sources'/ident/(ident+'.blend'),source_art/ident/(ident+'.blend'));copy(assets/'Models'/(ident+'.fbx'),source_art/ident/(ident+'.fbx'))
        for extension in ('.fbx','.fbx.meta'):copy(assets/'Models'/(ident+extension),project/'Assets/Models'/(ident+extension))
        for name in (ident+'.prefab',ident+'_Drop.prefab',ident+'_Drop.asset',ident+'.controller'):
            for suffix in ('','.meta'):
                p=assets/'Generated'/(name+suffix)
                if p.exists():copy(p,project/'Assets/Generated'/(name+suffix))
        entry.update(art_revision='WeaponRebuild20261026',visual_revision=3,art_project=str(STAGE),triangles={'Weapon_LOD'+str(i):v for i,v in enumerate(info['triangles'])},status='Reconstructed weapon design and original detailed materials; rig/action/socket contract preserved; offline checks and bundle reload passed; in-game review pending')
        temp=STAGE/'Sources'/ident/'asset-manifest.json';temp.write_text(json.dumps(entry,indent=2));copy(temp,source_art/ident/'asset-manifest.json')
    for channel in ('Atlas','Normal','Metallic','Occlusion','Emission'):
        p=assets/'RebuiltWeaponTextures'/(channel+'.png');copy(p,source_art/('ForestWeapon'+channel+'.png'));copy(p,project/'Assets'/('ForestWeapon'+channel+'.png'))
    for name in ('WeaponSurface.shader','RebuiltWeaponSurface.mat'):
        for suffix in ('','.meta'):copy(assets/(name+suffix),project/'Assets'/(name+suffix))
    for p in (assets/'RebuiltWeaponTextures').iterdir():
        if p.is_file():copy(p,project/'Assets/RebuiltWeaponTextures'/p.name)
    for name in ('forestweapons.unity3d','forestweapons.unity3d.manifest'):copy(STAGE/'Bundle'/name,ROOT/'artifacts/forest-weapons/Bundle'/name)
    copy(STAGE/'Delivery/Resources/forestweapons.unity3d',ROOT/'src/ZDelvePresentation/Resources/forestweapons.unity3d')
    copy(assets/'Editor/BuildForestWeapons.cs',project/'Assets/Editor/BuildForestWeapons.cs');copy(STAGE/'UnityProject/Packages/manifest.json',project/'Packages/manifest.json')
    temp=STAGE/'Reports/catalogue-updated.json';temp.write_text(json.dumps(canonical,indent=2));copy(temp,source_art/'catalogue.json');copy(temp,project/'Assets/weapon-rebuild.json')
    provenance=STAGE/'Artwork/PROVENANCE.txt';provenance.write_text('Original reconstructed geometry, material UVs, skin weights, short-range geometric occlusion and three LODs. Existing project-authored rigs and action data retained. Original material artwork generated with the built-in image_gen tool; exact prompt in '+str(STAGE/'Artwork/prompt.txt')+'. Original returned bitmap retained under Artwork. Five material maps; micro normals derived from texture gradients, not a high-poly bake. No native game geometry, textures or animation clips copied. Primary generators: tools/art/rebuild_weapon_models.py and tools/art/WeaponRebuild.cs.\n');copy(provenance,source_art/'PROVENANCE.txt')
    for p in icons.glob('*.png'):copy(p,ROOT/'src/ZZZZDelveBatch02/UIAtlases/ItemIconAtlas'/p.name)
    path=ROOT/'src/ZZZZDelveBatch02/Config/items.xml';text=path.read_text();ops=E.Element('configs')
    for ident in [s['id'] for s in specs]+list(aliases):
        xp="/items/item[@name='"+ident+"']"
        for key in ('CustomIcon','CustomIconTint'):E.SubElement(ops,'remove',xpath=xp+"/property[@name='"+key+"']")
        append=E.SubElement(ops,'append',xpath=xp);E.SubElement(append,'property',name='CustomIcon',value=ident);E.SubElement(append,'property',name='CustomIconTint',value='FFFFFF')
    fragment='\n<!-- WeaponRebuild20261026: matching model renders and neutral icon colors. -->\n'+''.join(E.tostring(child,encoding='unicode')+'\n' for child in ops);text=text.replace('</configs>',fragment+'</configs>');E.fromstring(text);temp=STAGE/'Reports/icon-items.xml';temp.write_text(text);copy(temp,path)
    assert all(sha(ROOT/p)==record['after'] for p,record in files.items())
    # Core actions, current held fixes, presentation DLL and installed-release pointer stay exact.
    for p,digest in baseline.items():
        if p not in ('src/Art/ForestWeapons/catalogue.json','src/ZDelvePresentation/Resources/forestweapons.unity3d',pointer):assert sha(ROOT/p)==digest,p
    assert pointer not in files
    (STAGE/'Reports/release-preservation.json').write_text(json.dumps({'release_at_integration_start':release_at_start,'release_at_integration_end':(ROOT/pointer).read_text().strip(),'release_pointer_written_by_this_task':False,'note':'A newer release was created concurrently; all core weapon/grip source hashes still matched. Existing release and installed game were preserved.'},indent=2))
    (STAGE/'Reports/source-integration.json').write_text(json.dumps({'scope':'source models, source weapon bundle, icons and repeatable build inputs; installed release unchanged','files':files},indent=2));print('Integrated',len(files),'source/build files with original backups')
manifest={str(p.relative_to(STAGE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted((STAGE/'Delivery').rglob('*')) if p.is_file()}
(STAGE/'Reports/delivery-hashes.json').write_text(json.dumps(manifest,indent=2))
report='''WeaponRebuild20261026

37 reconstructed models: 20 weapons/focuses, 13 runes and 4 ammunition variants. Four aliases preserve their existing mappings and receive matching icons (41 transparent 256px icons total). 14 original bones per source and 189 clips preserved. Three LODs, existing grips and six socket transforms retained. Existing 20 effects preserved.

Construction: bone field dagger, forged dagger with actual recessed fuller and honed bevels, asymmetric oak cudgel, beveled flanged mace, fitted spear sockets, contoured leather and iron knuckle guards with stitches/buckles, laminated bow limbs and weighted drawstrings, carved crossbow tiller/bolt rails/trigger/stirrup, carved magic shafts and totem bodies with fitted faceted mineral settings, physical rune strokes, cut feather vanes and bound projectile points. Field and Forged finishes differ.

Surfaces: five shared 2048x2048 maps (albedo, micro normal, metallic/smoothness, occlusion and emission). Original artwork made with the built-in image_gen tool; exact prompt in Artwork/prompt.txt and returned original in Artwork/WeaponMaterials-original.png. Texture gradients provide restrained micro normals; these are not high-poly baked normals. Blade bevels, fullers, fittings, stitches and bindings are actual geometry. Vertex colors carry part variation and short-range geometric occlusion. No native meshes/textures/clips copied.

Validation: Unity import/render, normalized weights, finite deformation at five times per clip, UV/tangent/color coverage, decreasing LOD budgets, authored grip/socket checks, matching static drops. Actual exported bundle reloaded: 94 original prefab addresses, 37 supported weapon surfaces, 189 clips, bounded existing effects and ten simulations of the current dagger/spear/staff/totem grip corrections. See unity-validation.txt, bundle-validation.txt and held-corrections.txt.

Visual review corrected a detached dagger pommel, crossbow side and cap UV stretching, inward blade/bevel normals, open wrap ends, angular knuckle outlines, and reduced-LOD UV extrapolation. Closed fittings also verify consistent edge winding during generation. Before/after lighting differs; gallery images are not a controlled engine benchmark.

Source integration: source-integration.json records pre/post hashes; SourceBackup preserves original files. Canonical Blender/FBX models, source material maps, weapon bundle, matching source icons and prop-builder inputs updated for the next package. Current held runtime/DLL, core action definitions, installed release pointer, installed playtest, saves, damage/recipes and skill behavior were not changed. Legacy generation is guarded against overwriting this reconstruction.

Remaining verification: actual first-person hands and clipping, in-game lighting/combat, save/reload, multiplayer and CPU/GPU performance. Offline checks do not certify vanilla artistic parity. The user requested continued work without hands-on UI testing.

Primary project: D:/Projects/Codex/7DaysToDelve/WeaponRebuild20261026
Rebuild geometry: tools/art/rebuild_weapon_models.py
Unity import/export: tools/art/WeaponRebuild.cs (Run, then Verify in separate editor process)
'''
(STAGE/'Reports/README.txt').write_text(report)
print('Packaged',len(specs),'models, 41 icons, 20 animation GIFs and',len(manifest),'delivery hashes')
