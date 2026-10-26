using System;
using System.IO;
using System.Xml;
using System.Collections.Generic;
public class ConsoleCmdPrefabAudit:ConsoleCmdAbstract
{
    public override string[] getCommands(){return new[]{"prefabaudit"};}
    public override string getDescription(){return "Check every placed prefab for unresolved native block references.";}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        try {
            var mod=ModManager.GetMod("AlliumTools",true);
            string world=File.ReadAllText(Path.Combine(mod.Path,"world-name.txt")).Trim();
            var doc=new XmlDocument();doc.Load(Path.GetFullPath(Path.Combine(mod.Path,"../../GeneratedWorlds/"+world+"/prefabs.xml")));
            var seen=new HashSet<string>();int cells=0;
            if(args.Count>0){doc.LoadXml("<prefabs/>");foreach(string name in args){var entry=doc.CreateElement("decoration");entry.SetAttribute("name",name);doc.DocumentElement.AppendChild(entry);}}
            foreach(XmlElement entry in doc.SelectNodes("/prefabs/decoration")) {
                string name=entry.GetAttribute("name");if(!seen.Add(name))continue;
                var prefab=new Prefab();if(!prefab.Load(name,true,true,false,false))throw new Exception("Cannot load "+name);
                for(int rotation=0;rotation<(args.Count>0?4:1);rotation++) {
                    var rotated=rotation==0?prefab:prefab.Clone(false);if(rotation>0)rotated.RotateY(true,rotation);
                    for(int y=0;y<rotated.size.y;y++)for(int z=0;z<rotated.size.z;z++)for(int x=0;x<rotated.size.x;x++) {
                        var block=rotated.GetBlock(x,y,z);
                        if(!block.isair && block.Block==null)throw new Exception("Unresolved block "+name+" rotation="+rotation+" at "+x+","+y+","+z+" type="+block.type);
                        cells++;
                    }
                }
            }
            SdtdConsole.Instance.Output("[PrefabAudit] PASS "+seen.Count+" unique placed prefabs; "+cells+" block references resolve.");
        }catch(Exception ex){SdtdConsole.Instance.Output("[PrefabAudit] FAIL "+ex);}
    }
}
