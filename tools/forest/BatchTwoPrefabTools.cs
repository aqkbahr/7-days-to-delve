using System;using System.IO;using System.Xml;using System.Collections.Generic;using UnityEngine;
public class ConsoleCmdBatchTwoPrefabs:ConsoleCmdAbstract {
 public override string[] getCommands(){return new[]{"batchtwoprefabs"};}
 public override string getDescription(){return "Isolated batch two prefab repair and native container parity audit.";}
 public override void Execute(List<string> args,CommandSenderInfo sender){try{
  string folder=Path.Combine(GameIO.GetUserGameDataDir(),"BatchTwoTools");
  var storage=new HashSet<string>(File.ReadAllLines(Path.Combine(folder,"storage-blocks.txt")));
  var map=new Dictionary<string,string>();var doc=new XmlDocument();doc.Load(Path.Combine(folder,"container-map.xml"));foreach(XmlElement e in doc.SelectNodes("/containers/container"))map[e.GetAttribute("source")]=e.GetAttribute("target");
  var pairs=new Dictionary<string,string>();foreach(string file in new[]{"forest-art-report.xml","arbor-art-report.xml","dungeon-art-report.xml"}){doc.Load(Path.Combine(folder,file));foreach(XmlElement e in doc.SelectNodes("/*/prefab"))pairs[e.GetAttribute("target")]=e.GetAttribute("source");}
  foreach(string target in new[]{"delve_forest_cabin_01_garden","delve_forest_cabin_04_garden","delve_forest_farm_12_garden"})pairs[target]=pairs[target.Replace("_garden","")];
  var report=new XmlDocument();report.LoadXml("<batchTwoPrefabs/>");int changed=0,checkedCount=0;var missing=new List<string>();
  foreach(var pair in pairs){
   var original=new Prefab();var p=new Prefab();if(!original.Load(pair.Value,true,true,false,false)||!p.Load(pair.Key,true,true,false,false))throw new Exception("Load "+pair.Key);
   var row=report.CreateElement("prefab");row.SetAttribute("name",pair.Key);row.SetAttribute("source",pair.Value);report.DocumentElement.AppendChild(row);int native=0,retained=0;
   for(int y=0;y<original.size.y;y++)for(int z=0;z<original.size.z;z++)for(int x=0;x<original.size.x;x++){
    var old=original.GetBlock(x,y,z);if(old.isair||old.ischild)continue;string name=old.Block.GetBlockName();bool container=storage.Contains(name);if(container)native++;
    string replacement;bool wagon=container&&(name.StartsWith("cars")||name.StartsWith("carWreck")||name.StartsWith("cntCar")||name.StartsWith("cntSedan")||name.StartsWith("cntServiceTruck")||name.StartsWith("tractor"));if(wagon)replacement=name;else map.TryGetValue(name,out replacement);if(replacement!=null){
     var before=p.GetBlock(x,y,z);var after=Block.GetBlockValue(replacement,false);if(after.isair)throw new Exception("Undefined "+replacement);
     if(before.ischild)throw new Exception("Container overlaps child "+pair.Key+" "+x+","+y+","+z);
     // Final art pass already removed appliance children. Keep unrelated cell data.
     if(before.Block.isMultiBlock)throw new Exception("Unexpected existing multiblock "+before.Block.GetBlockName());
     if(wagon)after.rotation=old.rotation;p.SetBlock(x,y,z,after);p.tileEntities.Remove(new Vector3i(x,y,z));
     var c=report.CreateElement("cell");c.SetAttribute("x",x.ToString());c.SetAttribute("y",y.ToString());c.SetAttribute("z",z.ToString());c.SetAttribute("before",before.Block.GetBlockName());c.SetAttribute("after",replacement);row.AppendChild(c);changed++;
    }
    if(container){var current=p.GetBlock(x,y,z);if(storage.Contains(current.Block.GetBlockName()))retained++;else missing.Add(pair.Key+" "+name+" at "+x+","+y+","+z+" now "+current.Block.GetBlockName());}
   }
   if(pair.Key=="delve_wayrest_forest"){
    var b=p.GetBlock(30,2,49);if(b.Block.GetBlockName()!="delveWayrestStewardSpawn")throw new Exception("Steward spawn moved");b.rotation=2;p.SetBlock(30,2,49,b);
   }
   row.SetAttribute("nativeContainers",native.ToString());row.SetAttribute("retainedContainers",retained.ToString());
   p.AddAllChildBlocks();var loc=p.location;string metadata=File.ReadAllText(loc.FullPathNoExtension+".xml");if(!p.Save(loc,true))throw new Exception("Save "+pair.Key);File.WriteAllText(loc.FullPathNoExtension+".xml",metadata);
   var reload=new Prefab();if(!reload.Load(loc,true,true,false,false))throw new Exception("Reload "+pair.Key);
   foreach(XmlElement c in row.SelectNodes("cell"))if(reload.GetBlock(int.Parse(c.GetAttribute("x")),int.Parse(c.GetAttribute("y")),int.Parse(c.GetAttribute("z"))).Block.GetBlockName()!=c.GetAttribute("after"))throw new Exception("Serialization mismatch "+pair.Key);
   checkedCount++;
  }
  report.Save(Path.Combine(folder,"prefab-repair-report.xml"));File.WriteAllLines(Path.Combine(folder,"missing-containers.txt"),missing);if(missing.Count>0)throw new Exception(missing.Count+" missing native containers; see missing-containers.txt");SdtdConsole.Instance.Output("[BatchTwoPrefabs] PASS "+checkedCount+" prefab container parity audits; "+changed+" medieval replacements; steward yaw corrected.");
 }catch(Exception e){SdtdConsole.Instance.Output("[BatchTwoPrefabs] FAIL "+e);}}
}
