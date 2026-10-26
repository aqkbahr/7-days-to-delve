from pathlib import Path
import shutil,json,hashlib
root=Path(__file__).resolve().parents[2];stage=Path('D:/AlliumArt/QualityPass20261025');dest=stage/'Runtime';dest.mkdir(exist_ok=True)
files=['ForestPresentation.cs','EnemyRigs.generated.cs','HeldCatalog.generated.cs','HeldPresentation.cs','ForestEffects.cs']
for name in files:shutil.copy2(root/'src/Art'/name,dest/name)
(dest/'baseline-source-hashes.json').write_text(json.dumps({name:hashlib.sha256((root/'src/Art'/name).read_bytes()).hexdigest() for name in files},indent=2))
shutil.copy2(root/'tools/art/NativeBodyFoundation.cs',dest/'NativeBodyFoundation.cs')
p=dest/'ForestPresentation.cs';s=p.read_text()
s=s.replace('EntityAlive entity;Transform nativeRoot;', 'NativeBodyFoundation foundation;bool keepNativeBody;\n  EntityAlive entity;Transform nativeRoot;')
s=s.replace('void Clear(){if(originals!=null)', 'void Clear(){if(foundation!=null){foundation.Dispose();foundation=null;}keepNativeBody=false;if(originals!=null)')
s=s.replace('foreach(var r in originals)if(r!=null)r.forceRenderingOff=true;', 'keepNativeBody=NativeBodyFoundation.Enabled(Visual);\n   if(keepNativeBody){foundation=new NativeBodyFoundation();foundation.Apply(originals,id);Log.Out("[ForestArt] Native body retained for "+id+" tinted materials="+foundation.TintedMaterials);}\n   else foreach(var r in originals)if(r!=null)r.forceRenderingOff=true;')
assert 'keepNativeBody=NativeBodyFoundation.Enabled(Visual)' in s
p.write_text(s)
(stage/'Reports/runtime-stage.txt').write_text('STAGED only: native bodies retained when exact v1 prefab marker is present; unmarked legacy bundles retain old replacement behavior. Native shaders, skeletons, hitboxes, controllers, ragdolls and body LODs remain authoritative. Materials cloned only for supported _Color/_BaseColor tint; cleanup restores originals. No production source or DLL changed.\n')
print('STAGED native-body presentation sources',dest)
