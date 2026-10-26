"""Package visual evidence and integrate validated plant art into project sources only."""
from pathlib import Path
import json,hashlib,shutil,sys,html,xml.etree.ElementTree as E
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
STAGE=Path('D:/Projects/Codex/7DaysToDelve/PlantRebuild20261026')
specs=json.loads((STAGE/'plants.json').read_text())['assets']
families=('Bramble','Yarrow','Thyme','Mooncap')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
validation=(STAGE/'Reports/unity-validation.txt').read_text()
assert validation.startswith('PASS\n') and validation.count(' PASS ')==26
assert 'BUNDLE all 229 original addresses' in validation
assert (STAGE/'Reports/bundle-load-validation.txt').read_text().startswith('PASS '),'Exported bundle must pass reload before integration'
for s in specs:
    assert (STAGE/'Sources'/s['id']/'model.json').exists()
    icon=STAGE/'Delivery/UIAtlases/ItemIconAtlas'/(s['id']+'.png')
    im=Image.open(icon);assert im.mode=='RGBA' and im.size==(256,256)
    assert im.getchannel('A').getextrema()==(0,255)
# Seed blocks should show their new packet in inventory, not a tiny sprout.
for f in families:
    icons=STAGE/'Delivery/UIAtlases/ItemIconAtlas';shutil.copy2(icons/('plantedDelve'+f+'1_Seed.png'),icons/('plantedDelve'+f+'1.png'))
font_path=Path('C:/Windows/Fonts/segoeui.ttf')
font=ImageFont.truetype(str(font_path),26) if font_path.exists() else ImageFont.load_default()
small=ImageFont.truetype(str(font_path),19) if font_path.exists() else font
sheet=Image.new('RGB',(1600,510),'#111811');draw=ImageDraw.Draw(sheet)
for i,f in enumerate(families):
    im=Image.open(STAGE/'Review'/('plantedDelve'+f+'3Harvest')/'hero.png').convert('RGB');im.thumbnail((400,450));sheet.paste(im,(i*400,20));draw.text((i*400+22,465),f,fill='#e8e3d6',font=font)
sheet.save(STAGE/'Review/mature-plants.jpg',quality=95)
stages=Image.new('RGB',(1600,1800),'#111811');draw=ImageDraw.Draw(stages)
for row,f in enumerate(families):
    for col,suffix in enumerate(('1','2','3Harvest','HarvestedVisual')):
        im=Image.open(STAGE/'Review'/('plantedDelve'+f+suffix)/'stage.png').convert('RGB').resize((400,400));stages.paste(im,(col*400,row*450));draw.text((col*400+10,row*450+407),f+' — '+('Sprout','Growing','Harvestable','Harvested')[col],fill='white',font=small)
stages.save(STAGE/'Review/growth-stages.jpg',quality=94)
before=Image.new('RGB',(1024,4*555),'#111811');draw=ImageDraw.Draw(before)
for row,f in enumerate(families):
    ident='plantedDelve'+f+'3Harvest'
    for col,p in enumerate((ROOT/'artifacts/forest-props/RenderProfile'/ident/'hero.png',STAGE/'Review'/ident/'hero.png')):
        if p.exists():
            im=Image.open(p).convert('RGB').resize((512,512));before.paste(im,(col*512,row*555))
    draw.text((15,row*555+519),f+' — previous',fill='white',font=small);draw.text((527,row*555+519),f+' — rebuilt',fill='white',font=small)
before.save(STAGE/'Review/before-after.jpg',quality=94)
for f in families:
    folder=STAGE/'Review'/('plantedDelve'+f+'3Harvest');frames=[Image.open(p).convert('RGB') for p in sorted(folder.glob('sway-*.png'))]
    assert len(frames)==12
    frames[0].save(folder/'sway.gif',save_all=True,append_images=frames[1:],duration=250,loop=0)

cards=[]
for s in specs:
    ident=s['id'];info=json.loads((STAGE/'Sources'/ident/'model.json').read_text());pictures=''.join('<a href="Review/'+ident+'/'+p+'"><img loading="lazy" src="Review/'+ident+'/'+p+'"></a>' for p in ('hero.png','side.png','top.png'))
    cards.append('<article><h2>'+html.escape(ident)+'</h2><p>LOD triangles (Blender): '+str(info['triangles'])+' · '+str(info['clips'])+' clips</p><div>'+pictures+'</div></article>')
page='''<!doctype html><meta charset="utf-8"><title>Forest botanical rebuild</title><style>body{background:#111811;color:#e8e3d6;font:16px system-ui;margin:30px}h1{font-size:32px}h2{font-size:20px}article{padding:18px;background:#20291f;margin:20px 0}article div{display:flex}img{width:100%;max-width:430px}a{color:#b6d98c}p{line-height:1.55;max-width:1000px}.wide{max-width:1600px}.motion{display:flex}</style><h1>Forest botanical rebuild</h1><p>Four species rebuilt as actual botanical forms: serrated compound bramble foliage and drupelet fruit, feathered yarrow foliage and branched flower heads, opposite thyme leaves and lateral shoots, irregular mooncaps with continuous rims and gilled undersides. Original diffuse artwork, micro normal maps, per-leaf color variation and three LODs. Includes all sixteen growing/harvested states, four seed packets, four harvested ingredients and two dried herbs.</p><img class="wide" src="Review/mature-plants.jpg"><p><a href="Review/before-after.jpg">Previous / rebuilt comparison</a> · <a href="Review/growth-stages.jpg">All growth stages</a> · <a href="Reports/unity-validation.txt">Unity validation</a></p><p>Offline rendered previews. Before/after images have different review lighting; they demonstrate geometry and surface changes, not a controlled lighting comparison. In-game lighting, actual growth/harvest rewards and dense-scene FPS still require a playtest.</p><div class="motion">'''
page+=''.join('<a href="Review/plantedDelve'+f+'3Harvest/sway.gif"><img src="Review/plantedDelve'+f+'3Harvest/sway.gif"></a>' for f in families)+'</div>'+''.join(cards)
page=page.replace('<p>Offline rendered previews.','<p><a href="Reports/bundle-load-validation.txt">Exported bundle reload check</a> · <a href="Reports/README.txt">Source and integration report</a> · <a href="Artwork/PROVENANCE.txt">Original texture artwork, tool and prompt</a></p><p>Offline rendered previews.')
(STAGE/'gallery.html').write_text(page,encoding='utf-8')

if '--integrate' in sys.argv:
    baseline=json.loads((STAGE/'Reports/production-baseline.json').read_text())
    for relative,digest in baseline.items():assert sha(ROOT/relative)==digest,'Production changed during rebuild: '+relative
    backups=STAGE/'SourceBackup';replaced={}
    def copy_into(source,target):
        source,target=Path(source),Path(target)
        if target.exists() and source.read_bytes()==target.read_bytes():return
        rel=target.relative_to(ROOT)
        if target.exists():
            backup=backups/rel;backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,backup);replaced[str(rel)]={'before':sha(target)}
        else:replaced[str(rel)]={'before':None}
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);replaced[str(rel)]['after']=sha(target)
    source_art=ROOT/'src/Art/ForestProps';project=ROOT/'artifacts/forest-props/UnityProject/Assets';stage_assets=STAGE/'UnityProject/Assets'
    catalogue=json.loads((source_art/'catalogue.json').read_text());lookup={s['id']:s for s in catalogue['assets']}
    for s in specs:
        ident=s['id'];out=source_art/ident;info=json.loads((STAGE/'Sources'/ident/'model.json').read_text())
        copy_into(STAGE/'Sources'/ident/(ident+'.blend'),out/(ident+'.blend'))
        copy_into(stage_assets/'Models'/(ident+'.fbx'),out/(ident+'.fbx'))
        for ext in ('.fbx','.fbx.meta'):copy_into(stage_assets/'Models'/(ident+ext),project/'Models'/(ident+ext))
        for name in (ident+'.prefab',ident+'_Drop.prefab',ident+'_Drop.asset',ident+'.controller'):
            for ext in ('','.meta'):
                p=stage_assets/'Generated'/(name+ext)
                if p.exists():copy_into(p,project/'Generated'/(name+ext))
        entry=lookup[ident];entry.update(art_revision='BotanicalRebuild20261026',art_project=str(STAGE),triangles={'Prop_LOD'+str(i):v for i,v in enumerate(info['triangles'])},status='Rebuilt botanical geometry, original detailed surfaces, rig/clip contracts preserved; offline checks passed; in-game visual check pending')
        tmp=STAGE/'Sources'/ident/'asset-manifest.json';tmp.write_text(json.dumps(entry,indent=2));copy_into(tmp,out/'asset-manifest.json')
    for family in families:
        name='plantedDelve'+family+'3HarvestPlayer.prefab'
        for ext in ('','.meta'):copy_into(stage_assets/'Generated'/(name+ext),project/'Generated'/(name+ext))
    for name in ('PlantSurface.shader','BotanicalSurface.mat'):
        for ext in ('','.meta'):copy_into(stage_assets/(name+ext),project/(name+ext))
    for p in (stage_assets/'BotanicalTextures').iterdir():
        if p.is_file():copy_into(p,project/'BotanicalTextures'/p.name)
        if p.suffix=='.png':copy_into(p,source_art/'BotanicalTextures'/p.name)
    copy_into(STAGE/'plants.json',project/'botanical-models.json')
    copy_into(ROOT/'tools/art/BuildForestProps.cs',project/'Editor/BuildForestProps.cs')
    copy_into(STAGE/'Delivery/Resources/forestprops.unity3d',ROOT/'src/ZDelvePresentation/Resources/forestprops.unity3d')
    for p in (STAGE/'Delivery/UIAtlases/ItemIconAtlas').glob('*.png'):copy_into(p,ROOT/'src/ZZZZDelveBatch02/UIAtlases/ItemIconAtlas'/p.name)
    for tag in ('blocks','items'):
        path=ROOT/'src/ZZZZDelveBatch02/Config'/(tag+'.xml');text=path.read_text();ops=E.Element('configs')
        targets=[]
        if tag=='blocks':targets=[('plantedDelve'+f+suffix,'plantedDelve'+f+('1' if suffix=='1' else '2' if suffix=='2' else '3Harvest')) for f in families for suffix in ('1','2','3Harvest','3HarvestPlayer')]
        else:targets=[(s['id'],s['id']) for s in specs if s['kind']=='item' and not s['id'].endswith('1_Seed')]
        for ident,icon in targets:
            xp='/'+tag+'/'+tag[:-1]+"[@name='"+ident+"']"
            for key in ('CustomIcon','CustomIconTint'):E.SubElement(ops,'remove',xpath=xp+"/property[@name='"+key+"']")
            append=E.SubElement(ops,'append',xpath=xp);E.SubElement(append,'property',name='CustomIcon',value=icon);E.SubElement(append,'property',name='CustomIconTint',value='FFFFFF')
        fragment='\n<!-- BotanicalRebuild20261026: matching botanical art and neutral icon tint. -->\n'+''.join(E.tostring(child,encoding='unicode')+'\n' for child in ops)
        text=text.replace('</configs>',fragment+'</configs>');E.fromstring(text);tmp=STAGE/'Reports'/('icon-'+tag+'.xml');tmp.write_text(text);copy_into(tmp,path)
    temp=STAGE/'Reports/catalogue-updated.json';temp.write_text(json.dumps(catalogue,indent=2));copy_into(temp,source_art/'catalogue.json')
    (STAGE/'Reports/source-integration.json').write_text(json.dumps({'scope':'canonical source art, source bundle, source icons, icon config, original prop build project; installed game and release untouched','files':replaced},indent=2))
    print('Integrated',len(replaced),'source/build inputs with byte-preserving backups')

if '--refresh-integration' in sys.argv:
    path=STAGE/'Reports/source-integration.json';info=json.loads(path.read_text());files=info['files']
    updates=[(STAGE/'Delivery/Resources/forestprops.unity3d',ROOT/'src/ZDelvePresentation/Resources/forestprops.unity3d'),(STAGE/'Bundle/forestprops.unity3d',ROOT/'artifacts/forest-props/Bundle/forestprops.unity3d'),(STAGE/'Bundle/forestprops.unity3d.manifest',ROOT/'artifacts/forest-props/Bundle/forestprops.unity3d.manifest'),(ROOT/'tools/art/BuildForestProps.cs',ROOT/'artifacts/forest-props/UnityProject/Assets/Editor/BuildForestProps.cs'),(STAGE/'UnityProject/Packages/manifest.json',ROOT/'artifacts/forest-props/UnityProject/Packages/manifest.json')]
    for source,target in updates:
        rel=str(target.relative_to(ROOT));assert target.exists()
        if rel in files:assert sha(target)==files[rel]['after'],'Concurrent source change: '+rel
        else:
            backup=STAGE/'SourceBackup'/rel;backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,backup);files[rel]={'before':sha(target)}
        shutil.copy2(source,target);files[rel]['after']=sha(target)
    assert all(sha(ROOT/p)==v['after'] for p,v in files.items())
    path.write_text(json.dumps(info,indent=2));print('Refreshed verified bundle and reproducible build settings;',len(files),'source hashes verified')
manifest={str(p.relative_to(STAGE)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted((STAGE/'Delivery').rglob('*')) if p.is_file()}
(STAGE/'Reports/delivery-hashes.json').write_text(json.dumps(manifest,indent=2))
prompt='''Built-in image_gen; new original bitmap artwork; no reference images. Prompt: Create an ORIGINAL production game botanical material atlas, flat diffuse albedo only, no lighting, no cast shadows, no perspective, no labels, no gaps or borders. Exactly 4 columns and 2 rows of equally sized square texture patches, seamless filling each cell. High photoreal macro botanical detail, muted natural colors for a realistic survival game. TOP ROW: bramble leaf tissue with a vertical main vein and woodland olive/yellow/reddish mottling; silvery sage yarrow tissue with fine pale veins; warm sage olive thyme tissue with delicate veins and speckles; cracked reddish brown bramble cane bark with pale lenticels. BOTTOM ROW: pale grey lavender mooncap skin with fine fibrous radial growth lines and muted lilac center; dense ivory beige radial mushroom gills; ivory beige fibrous stem with vertical grain and russet flecks; deep burgundy purple blackberry drupelet tissue with powdery bluish bloom. Flat full-cell texture patches, no plant silhouettes, labels, containers or scene. The exact full submitted prompt is also retained in this task's image_gen tool call. Artwork/BotanicalAtlas-original.png preserves the returned original. Pipeline extends the atlas with original procedural petal, pollen and flax swatches. Micro-normal is derived from texture gradients and is not a high-poly bake. All geometry is original. No native game meshes, textures or animations were copied into these assets.'''
(STAGE/'Artwork/PROVENANCE.txt').write_text(prompt)
report='''BotanicalRebuild20261026

26 rebuilt models: 16 plant stages, 4 seed packets, 4 fresh ingredients and 2 dried herbs. Four cultivated aliases share the new mature art. Single material per model and three mesh LODs. Original six-bone rigs and 58 animation clips retained; plant controllers now default to looping Sway. Updated inventory/drop representations and 26 transparent icons.

Geometry: curved serrated compound bramble leaves, thorned canes, 3D drupelet berries, feathered yarrow leaves, branched corymb flower heads and basal foliage, opposite thyme leaves with lateral shoots, curved mooncap stipes, domed irregular caps, continuous cap rims, radial gill detail. Fresh and dried herb color states differ.

Surface: original generated diffuse artwork, procedural petal/pollen/flax patches, image-derived micro normals, per-part vertex color and height occlusion, double-sided leaf shader. Maps are 2048x1536; one shared botanical material. No native texture or mesh redistribution.

Checks: all 26 passed offline Unity import, finite deformations at five times per clip, normalized weights, UV/tangent/color presence, decreasing LOD triangles, footprint bounds, 16 harvesting collider ray checks, matching drops and 229 original bundle addresses. Alpha icons verified. See unity-validation.txt. The actual exported bundle was reopened: all 229 prefabs/material references resolved; 26 supported botanical surfaces, 16 default Sway states and solid harvesting colliders, and 58 clips without gameplay callbacks verified (bundle-load-validation.txt). The initial build from a minimal project failed reload; a clean rebuild with the full module manifest passed. Previews and sway GIFs reviewed; mushroom rim gaps, sparse thyme branches and detached bramble blossoms corrected during review.

Integration: see source-integration.json for canonical source changes and pre/post hashes. Original files are backed up under SourceBackup. Source models/catalogue, source art bundle, icon atlas/config and original prop builder inputs updated for the next release. Installed playtest, release pointer, saves, gameplay values, recipes, growth timers and harvest rewards were not modified. Legacy geometry generation preserves art_revision-marked botanical models; rebuild these using rebuild_botanical_models.py and PlantRebuild.Run.

Remaining verification: actual in-game material lighting, growth/harvest behavior, dense-scene CPU/GPU performance, multiplayer and save/reload. Offline checks do not certify vanilla artistic parity or game performance. The models have been substantially rebuilt; visual comparison is in gallery.html.

Source project: D:/Projects/Codex/7DaysToDelve/PlantRebuild20261026
Artwork provenance and prompt: Artwork/PROVENANCE.txt (built-in image_gen, no API fallback)
'''
(STAGE/'Reports/README.txt').write_text(report)
print('Packaged gallery, growth sheet, four sway GIFs, transparent icons and',len(manifest),'delivery hashes')
