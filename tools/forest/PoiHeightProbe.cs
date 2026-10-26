using System;using System.IO;using System.Xml;using System.Text;using System.Collections.Generic;
public class ConsoleCmdPoiHeight:ConsoleCmdAbstract {
 public override string[] getCommands(){return new[]{"poiheightaudit"};}
 public override string getDescription(){return "Read-only prefab perimeter terrain height audit.";}
 public override void Execute(List<string> args,CommandSenderInfo sender){try{
  var mod=ModManager.GetMod("PoiHeightProbe",true);var doc=new XmlDocument();doc.Load(Path.Combine(mod.Path,"prefabs.xml"));var report=new StringBuilder("prefab,groundY,yOffset,samples,medianSurfaceDelta\n");int count=0;
  foreach(XmlElement row in doc.SelectNodes("/prefabs/decoration")){
   var p=new Prefab();string name=row.GetAttribute("name");if(!p.Load(name,true,true,false,false))throw new Exception("Load "+name);var deltas=new List<float>();
   for(int z=0;z<p.size.z;z++)for(int x=0;x<p.size.x;x++){
    if(x>1&&z>1&&x<p.size.x-2&&z<p.size.z-2)continue;
    for(int y=Math.Min(p.size.y-1,-p.yOffset+2);y>=0;y--){var b=p.GetBlock(x,y,z);if(b.isair||b.Block==null||!b.Block.shape.IsTerrain())continue;
     // Exact native copyPrefabsIntoHeightMap density-to-surface calculation.
     deltas.Add(p.yOffset+y+(-p.GetDensity(x,y,z)/128f)-1f);break;
    }
   }
   deltas.Sort();report.AppendLine(name+","+row.GetAttribute("position").Split(',')[1]+","+p.yOffset+","+deltas.Count+","+(deltas.Count==0?"NA":deltas[deltas.Count/2].ToString(System.Globalization.CultureInfo.InvariantCulture)));count++;
  }
  File.WriteAllText(Path.Combine(mod.Path,"height-audit.csv"),report.ToString());SdtdConsole.Instance.Output("[PoiHeight] PASS read-only perimeter audit "+count+" placed prefabs.");
 }catch(Exception ex){SdtdConsole.Instance.Output("[PoiHeight] FAIL "+ex);}}
}
