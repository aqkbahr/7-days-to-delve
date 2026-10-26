from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-05-complete/art';P=A/'UnityProject'
for d in ['Assets/Editor','ProjectSettings','Packages']:(P/d).mkdir(parents=True,exist_ok=True)
for name in ['Packages/manifest.json','ProjectSettings/ProjectVersion.txt']:shutil.copy2(R/'artifacts/batch-05/art/UnityProject'/name,P/name)
s=(R/'tools/art/BuildBatchFour.cs').read_text().replace('BuildBatchFour','BuildBatchFiveWorldArt')
start=s.index(' static GameObject Chest(');end=s.index(' public static void Run()',start)
s=s[:start]+''' static GameObject Chest(bool unused){var g=new GameObject("delveIronboundCrate");g.tag="T_Block";
 // All boards and straps fit within exactly one voxel, including the collider.
 for(int i=0;i<6;i++){float h=(i+.5f)/6;
  for(int side=-1;side<=1;side+=2){
   Part(g,"SidePlank",PrimitiveType.Cube,new Vector3(side*.475f,h,0),new Vector3(.04f,.162f,.95f),wood);
   Part(g,"EndPlank",PrimitiveType.Cube,new Vector3(0,h,side*.475f),new Vector3(.95f,.162f,.04f),wood);
  }
  for(int side=-1;side<=1;side+=2)Part(g,"TopBottom",PrimitiveType.Cube,new Vector3((i-2.5f)/6,.5f+side*.48f,0),new Vector3(.162f,.04f,.96f),wood);
 }
 foreach(float a in new[]{-.35f,.35f})for(int side=-1;side<=1;side+=2){
  Part(g,"EndBand",PrimitiveType.Cube,new Vector3(a,.5f,side*.49f),new Vector3(.055f,1,.02f),iron);
  Part(g,"SideBand",PrimitiveType.Cube,new Vector3(side*.49f,.5f,a),new Vector3(.02f,1,.055f),iron);
  Part(g,"TopBand",PrimitiveType.Cube,new Vector3(a,.99f,0),new Vector3(.055f,.02f,1),iron);
 }
 return g;
 }
''' +s[end:]
s=s.replace('variant<2','variant<1').replace('c.center=new Vector3(0,.38f,0);c.size=new Vector3(.95f,.76f,.65f)','c.center=new Vector3(0,.5f,0);c.size=Vector3.one').replace('batchfour.unity3d','batchfiveworld.unity3d').replace('PASS two textured crate-stack prefabs and icons','PASS full one-metre ironbound supply crate mesh, collider and icon')
(R/'tools/art/BuildBatchFiveWorldArt.cs').write_text(s)
(P/'Assets/Editor/BuildBatchFiveWorldArt.cs').write_text(s)
print(P)
