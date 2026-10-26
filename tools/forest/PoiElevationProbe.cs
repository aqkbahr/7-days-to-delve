using System;
using System.Collections.Generic;
using System.IO;
using System.Xml;
public class PoiElevationProbe:IModApi {
 public static string Output;
 public void InitMod(Mod mod){Output=Path.GetFullPath(Path.Combine(mod.Path,"../../elevation.csv"));}
}
public class ConsoleCmdPoiElevation:ConsoleCmdAbstract {
 static ChunkManager.ChunkObserver observer;
 public override string[] getCommands(){return new[]{"poielevation"};}
 public override string getDescription(){return "Read-only prefab edge terrain survey";}
 public override void Execute(List<string> args,CommandSenderInfo sender){try{
  var w=GameManager.Instance.World;
  if(args.Count>=3){int x=int.Parse(args[1]),z=int.Parse(args[2]);
   if(args[0]=="load"){if(observer!=null)GameManager.Instance.RemoveChunkObserver(observer);observer=GameManager.Instance.AddChunkObserver(new UnityEngine.Vector3(x,80,z),false,4,3);SdtdConsole.Instance.Output("[PoiElevation] requested");return;}
   int top=w.GetHeight(x,z);SdtdConsole.Instance.Output("[PoiElevation] column "+x+","+z+" height="+top+" raw="+w.GetHeightAt(x,z));
   for(int y=top-4;y<=top+1;y++)SdtdConsole.Instance.Output(y+" "+w.GetBlock(x,y,z).Block.GetBlockName()+" density="+w.GetDensity(x,y,z));return;
  }
  var sites=new List<PrefabInstance>();w.GetPOIsAtXZ(-4096,4096,-4096,4096,sites);
  var lines=new List<string>{"name,x,y,z,yoffset,edge_y,edge_density,count"};
  foreach(var site in sites){
   string name=site.location.FileNameNoExtension;if(name.StartsWith("delve_ore_"))continue;
   var p=w.m_PrefabCache.GetPrefab(name,true,true,false,false);if(p==null)continue;
   var counts=new SortedDictionary<string,int>();
   for(int z=0;z<p.size.z;z++)for(int x=0;x<p.size.x;x++){
    if(x!=0&&z!=0&&x!=p.size.x-1&&z!=p.size.z-1)continue;
    for(int y=Math.Min(p.size.y-1,-p.yOffset+3);y>=Math.Max(0,-p.yOffset-5);y--){
     var b=p.GetBlock(x,y,z);if(!b.isair&&b.Block.shape.IsTerrain()){
      string key=y+","+p.GetDensity(x,y,z);if(!counts.ContainsKey(key))counts[key]=0;counts[key]++;break;
     }
    }
   }
   foreach(var kv in counts)lines.Add(name+","+site.boundingBoxPosition.x+","+site.boundingBoxPosition.y+","+site.boundingBoxPosition.z+","+p.yOffset+","+kv.Key+","+kv.Value);
  }
  File.WriteAllLines(PoiElevationProbe.Output,lines.ToArray());SdtdConsole.Instance.Output("[PoiElevation] PASS surveyed "+sites.Count+" placements: "+PoiElevationProbe.Output);
 }catch(Exception e){SdtdConsole.Instance.Output("[PoiElevation] FAIL "+e);}}
}
