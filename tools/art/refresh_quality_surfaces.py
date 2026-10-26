import bpy,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from quality_surfaces import build_surfaces
stage=Path('D:/AlliumArt/QualityPass20261025');models=json.loads((stage/'inventory.json').read_text())['models'];done=set()
for spec in models:
 if not spec['blend']:continue
 identity=spec['id'] if spec['group'] in ('enemies','quadrupeds','thornback') else spec['group']
 if identity in done:continue
 for image in list(bpy.data.images):bpy.data.images.remove(image)
 build_surfaces(bpy,str(stage/'UnityProject/Assets/Legacy'/spec['group']/spec['texture']),spec['group'],spec['id'],str(stage/'UnityProject/Assets/QualitySurfaces'/identity));done.add(identity)
 (stage/'Reports/surface-progress.txt').write_text('REFRESHED '+identity)
for spec in models:
 path=Path(spec['destination'])/(spec['id']+'.blend')
 if not path.exists():continue
 bpy.ops.wm.open_mainfile(filepath=str(path))
 for image in bpy.data.images:
  if 'QualitySurfaces' not in image.filepath:continue
  if image.packed_file:image.unpack(method='REMOVE')
  image.reload()
 bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
(stage/'Reports/surface-progress.txt').write_text('PASS organic multiscale surfaces; linked editable sources refreshed; '+str(len(done))+' surface sets')
