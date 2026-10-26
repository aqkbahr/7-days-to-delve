using System;
using System.IO;
using System.Xml;
using System.Collections.Generic;
using UnityEngine;

public class ConsoleCmdOreBuild : ConsoleCmdAbstract
{
    internal static readonly string[] Names={"iron","coal","lead","nitrate","shale"};
    internal static readonly string[] Ores={"terrOreIron","terrOreCoal","terrOreLead","terrOrePotassiumNitrate","terrOreOilDeposit"};
    internal static readonly string[] Markers={"oreIronBoulder","oreCoalBoulder","oreLeadBoulder","orePotassiumNitrateBoulder","oreShaleBoulder"};
    public override string[] getCommands(){return new[]{"orebuild"};}
    public override string getDescription(){return "Author native-block marked mineral veins; development only.";}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        try {
            var mod=ModManager.GetMod("DelveWayrest",true);
            var report=new XmlDocument();report.LoadXml("<oreBuild/>");
            for(int k=0;k<Names.Length;k++) {
                Prefab p=new Prefab(new Vector3i(13,24,13));
                p.bCopyAirBlocks=false;p.bAllowDecorations=false;p.bExcludeDistantPOIMesh=true;
                p.yOffset=-22;p.DifficultyTier=0;p.tags=FastTags<TagGroup.Poi>.Parse("biomeonly,devonly");
                BlockValue ore=Block.GetBlockValue(Ores[k],false),marker=Block.GetBlockValue(Markers[k],false);
                if(ore.isair||marker.isair)throw new Exception("Missing ore definitions");
                int count=0;
                // Two overlapping lobes form a connected, irregular underground vein.
                // A two-cell-wide seam rises to the native surface indicator.
                for(int y=1;y<=21;y++)for(int z=1;z<=11;z++)for(int x=1;x<=11;x++) {
                    double a=Math.Pow((x-5.0)/4.2,2)+Math.Pow((y-8.0)/6.2,2)+Math.Pow((z-6.0)/4.5,2);
                    double b=Math.Pow((x-8.0)/3.0,2)+Math.Pow((y-12.0)/4.5,2)+Math.Pow((z-5.0)/3.2,2);
                    bool seam=(x==6||x==7)&&(z==6||z==7)&&y>=9;
                    if(a<=1||b<=1||seam){p.SetBlock(x,y,z,ore);p.SetDensity(x,y,z,-127);count++;}
                    else if(Math.Min(a,b)<=1.3){p.SetBlock(x,y,z,Block.GetBlockValue("terrGravel",false));p.SetDensity(x,y,z,-127);}
                }
                p.SetBlock(6,22,6,marker);p.AddAllChildBlocks();
                var loc=PathAbstractions.PrefabsSearchPaths.BuildLocation((PathAbstractions.EAbstractedLocationType)3,"POIs","delve_ore_"+Names[k],mod,null).Value;
                if(!p.Save(loc,true))throw new Exception("Save failed");
                p.AddAllChildBlocks();Prefab check=new Prefab();if(!check.Load(loc,true,true,false,false))throw new Exception("Reload failed");
                for(int y=0;y<24;y++)for(int z=0;z<13;z++)for(int x=0;x<13;x++)
                    if(p.GetBlock(x,y,z).rawData!=check.GetBlock(x,y,z).rawData)throw new Exception("Serialization mismatch");
                // Verify the marker's seam connects to every ore block, not a detached rock.
                var seen=new HashSet<Vector3i>();var q=new Queue<Vector3i>();var start=new Vector3i(6,21,6);seen.Add(start);q.Enqueue(start);
                Vector3i[] dirs={new Vector3i(1,0,0),new Vector3i(-1,0,0),new Vector3i(0,1,0),new Vector3i(0,-1,0),new Vector3i(0,0,1),new Vector3i(0,0,-1)};
                while(q.Count>0){var pos=q.Dequeue();foreach(var d in dirs){var n=pos+d;if(n.x<0||n.y<0||n.z<0||n.x>=13||n.y>=24||n.z>=13||seen.Contains(n))continue;if(check.GetBlock(n.x,n.y,n.z).type==ore.type){seen.Add(n);q.Enqueue(n);}}}
                if(seen.Count!=count)throw new Exception("Disconnected vein");
                var e=report.CreateElement("vein");e.SetAttribute("name",Names[k]);e.SetAttribute("oreBlocks",count.ToString());e.SetAttribute("marker",Markers[k]);report.DocumentElement.AppendChild(e);
                SdtdConsole.Instance.Output("[Ore] PASS "+Names[k]+" connected ore blocks="+count+" marker="+Markers[k]);
            }
            report.Save(Path.Combine(ModManager.GetMod("AlliumTools",true).Path,"ore-build-report.xml"));
        }catch(Exception ex){SdtdConsole.Instance.Output("[Ore] FAIL "+ex);}
    }
}

public class ConsoleCmdOreVerify : ConsoleCmdAbstract
{
    static ChunkManager.ChunkObserver observer;
    public override string[] getCommands(){return new[]{"oreverify"};}
    public override string getDescription(){return "oreverify load|check x groundY z resourceIndex; verifies generated marker and entire buried deposit.";}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        try {
            var w=GameManager.Instance.World;int x=int.Parse(args[1]),ground=int.Parse(args[2]),z=int.Parse(args[3]),k=int.Parse(args[4]);
            if(args[0]=="load") {
                if(observer!=null)GameManager.Instance.RemoveChunkObserver(observer);
                observer=GameManager.Instance.AddChunkObserver(new Vector3(x,ground+2,z),false,2,2);
                SdtdConsole.Instance.Output("[Ore] Loading "+ConsoleCmdOreBuild.Names[k]+" at "+x+","+ground+","+z);return;
            }
            var marker=w.GetBlock(x,ground,z);
            if(marker.Block.GetBlockName()!=ConsoleCmdOreBuild.Markers[k])throw new Exception("Missing surface marker at "+x+","+ground+","+z+": "+marker.Block.GetBlockName());
            if(w.GetWaterPercent(new Vector3i(x,ground,z))>0)throw new Exception("Submerged marker");
            Prefab p=new Prefab();if(!p.Load("delve_ore_"+ConsoleCmdOreBuild.Names[k],true,true,false,false))throw new Exception("Missing vein prefab");
            int ore=Block.GetBlockValue(ConsoleCmdOreBuild.Ores[k],false).type,count=0;
            for(int yy=0;yy<22;yy++)for(int zz=0;zz<13;zz++)for(int xx=0;xx<13;xx++) {
                if(p.GetBlock(xx,yy,zz).type!=ore)continue;
                if(w.GetBlock(x-6+xx,ground-22+yy,z-6+zz).type!=ore)throw new Exception("Missing buried ore at "+xx+","+yy+","+zz);
                count++;
            }
            SdtdConsole.Instance.Output("[Ore] PASS "+ConsoleCmdOreBuild.Names[k]+" "+w.GetBiomeInWorld(x,z).m_sBiomeName+" at "+x+","+ground+","+z+" surface marker + "+count+" connected underground ore blocks");
        }catch(Exception ex){SdtdConsole.Instance.Output("[Ore] FAIL "+ex);}
    }
}
