using System;using System.IO;using System.Xml;using System.Collections.Generic;
public static class BatchThreePrefabTools {
 static TextureFullArray Paint(int id){long p=0;for(int f=0;f<6;f++)p|=(long)id<<(f*8);return new TextureFullArray(p);}
 public static string Run(){string folder=Path.Combine(GameIO.GetUserGameDataDir(),"BatchThreeTools");var doc=new XmlDocument();doc.Load(Path.Combine(folder,"blueprint.xml"));var old=new Prefab();if(!old.Load("delve_wayrest_forest",true,true,false,false))throw new Exception("Wayrest missing");var p=new Prefab();if(!p.Load("delve_wayrest_forest",true,true,false,false))throw new Exception("Editable Wayrest missing");var authored=new Prefab(new Vector3i(60,18,60));
 foreach(XmlElement row in doc.DocumentElement.ChildNodes){var b=Block.GetBlockValue(row.GetAttribute("block"),false);if(b.isair)throw new Exception("Unknown block "+row.GetAttribute("block"));b.rotation=byte.Parse(row.GetAttribute("rotation"));b.damage=int.Parse(row.GetAttribute("damage"));if(b.Block.GetBlockName()=="delveWayrestStewardSpawn")b.rotation=2;for(int x=int.Parse(row.GetAttribute("x"));x<=int.Parse(row.GetAttribute("end"));x++){int y=int.Parse(row.GetAttribute("y")),z=int.Parse(row.GetAttribute("z"));authored.SetBlock(x,y,z,b);}}
 int preserved=0;for(int y=0;y<18;y++)for(int z=0;z<60;z++)for(int x=0;x<60;x++){var before=old.GetBlock(x,y,z);string n=before.Block.GetBlockName();var after=authored.GetBlock(x,y,z);
 // Keep existing furnishings, services and their native tile entities in place.
 if(!before.isair&&!before.isTerrain&&!n.Contains("Shapes:")&&n!="woodLogPillar100"&&y>=2){after=before;preserved++;}
 p.SetBlock(x,y,z,after);p.SetDensity(x,y,z,after.isTerrain?(sbyte)-127:(sbyte)127);
 string name=after.Block.GetBlockName();if(name.Contains("Shapes:"))p.SetTexture(x,y,z,Paint(name.StartsWith("wood")?(y>=7?17:((x+z)%5==0?67:68)):63));
 }
 p.AddAllChildBlocks();var changes=new XmlDocument();changes.LoadXml("<wayrestChanges/>");int count=0;
 for(int y=0;y<18;y++)for(int z=0;z<60;z++)for(int x=0;x<60;x++){var a=old.GetBlock(x,y,z);var b=p.GetBlock(x,y,z);if(a.isair&&b.isair&&old.GetDensity(x,y,z)==p.GetDensity(x,y,z))continue;var e=changes.CreateElement("cell");foreach(var pair in new Dictionary<string,string>{{"x",x.ToString()},{"y",y.ToString()},{"z",z.ToString()},{"before",a.Block.GetBlockName()},{"rotation",a.rotation.ToString()},{"damage",a.damage.ToString()},{"density",old.GetDensity(x,y,z).ToString()},{"after",b.Block.GetBlockName()}})e.SetAttribute(pair.Key,pair.Value);changes.DocumentElement.AppendChild(e);count++;}
 var loc=old.location;string metadata=File.ReadAllText(loc.FullPathNoExtension+".xml");if(!p.Save(loc,true))throw new Exception("Save failed");File.WriteAllText(loc.FullPathNoExtension+".xml",metadata);changes.Save(Path.Combine(folder,"wayrest-changes.xml"));File.WriteAllText(Path.Combine(folder,"prefab-result.txt"),"PASS Wayrest serialized; changes="+count+" preserved furnishings="+preserved);return "PASS Wayrest serialized "+count;
 }
}

