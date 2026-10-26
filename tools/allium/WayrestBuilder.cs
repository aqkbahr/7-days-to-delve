using System;
using System.IO;
using System.Xml;
using System.Collections.Generic;

// Development-only native prefab serializer. Not distributed to players.
public class ConsoleCmdWayrestBuild : ConsoleCmdAbstract
{
    public override string[] getCommands() { return new[] { "wayrestbuild" }; }
    public override string getDescription() { return "Serialize the authored Wayrest blueprint into the isolated DelveWayrest mod."; }
    public override void Execute(List<string> args, CommandSenderInfo sender)
    {
        try {
            Mod tools=ModManager.GetMod("AlliumTools",true);
            Mod target=ModManager.GetMod("DelveWayrest",true);
            XmlDocument doc=new XmlDocument();doc.Load(Path.Combine(tools.Path,"blueprint.xml"));
            Prefab p=new Prefab(new Vector3i(60,18,60));
            p.bCopyAirBlocks=true;p.bAllowDecorations=false;p.bTraderArea=true;
            p.bExcludeDistantPOIMesh=true;p.bExcludePOICulling=true;p.yOffset=-2;
            p.questTags=FastTags<TagGroup.Global>.Parse("trader, traderJoel");
            Dictionary<string,BlockValue> blocks=new Dictionary<string,BlockValue>();
            int count=0;
            foreach(XmlElement row in doc.DocumentElement.ChildNodes) {
                string name=row.GetAttribute("block");BlockValue value;
                if(!blocks.TryGetValue(name,out value)) {
                    value=Block.GetBlockValue(name,false);
                    if(value.isair) throw new InvalidDataException("Unknown block: "+name);
                    blocks.Add(name,value);
                }
                int x=int.Parse(row.GetAttribute("x")),end=int.Parse(row.GetAttribute("end"));
                int y=int.Parse(row.GetAttribute("y")),z=int.Parse(row.GetAttribute("z"));
                // Hall entrance is south (local z=39); steward stands at z=49.
                // Native BlockSpawnEntity uses 90 * block rotation as entity yaw.
                if(row.HasAttribute("rotation"))value.rotation=byte.Parse(row.GetAttribute("rotation"));
                if(row.HasAttribute("damage"))value.damage=int.Parse(row.GetAttribute("damage"));
                if(name=="delveWayrestStewardSpawn") value.rotation=2;
                for(;x<=end;x++) { p.SetBlock(x,y,z,value);p.SetDensity(x,y,z,value.isTerrain?(sbyte)-127:(sbyte)127);count++; }
            }
            p.indexedBlockOffsets["Trader"]=new List<Vector3i>{new Vector3i(30,2,49)};
            p.AddAllChildBlocks();
            var location=PathAbstractions.PrefabsSearchPaths.BuildLocation((PathAbstractions.EAbstractedLocationType)3,"POIs","delve_wayrest_01",target,null).Value;
            Directory.CreateDirectory(Path.GetDirectoryName(location.FullPath));
            if(!p.Save(location,true)) throw new IOException("Prefab save failed");
            // Explicit native metadata for overnight trader ejection and protected area.
            XmlDocument meta=new XmlDocument();meta.Load(location.FullPathNoExtension+".xml");
            Set(meta,"TeleportVolumeStart","1, 1, 1");Set(meta,"TeleportVolumeSize","58, 16, 58");
            Set(meta,"TraderArea","True");
            Set(meta,"TraderAreaProtect","0,0,0");Set(meta,"Tags","gateway, nocheckpoint");
            Set(meta,"EditorGroups","settlements");Set(meta,"ThemeTags","delveWayrest");
            meta.Save(location.FullPathNoExtension+".xml");
            SdtdConsole.Instance.Output("[Wayrest] PASS saved "+count+" authored blocks, "+blocks.Count+" types, one steward. "+location.FullPathNoExtension);
        } catch(Exception ex) { SdtdConsole.Instance.Output("[Wayrest] ERROR "+ex); }
    }
    static void Set(XmlDocument doc,string name,string value) {
        var node=doc.SelectSingleNode("/prefab/property[@name='"+name+"']") as XmlElement;
        if(node==null){node=doc.CreateElement("property");node.SetAttribute("name",name);doc.DocumentElement.AppendChild(node);}
        node.SetAttribute("value",value);
    }
}

public class ConsoleCmdWayrestVerify : ConsoleCmdAbstract
{
    public override string[] getCommands(){return new[]{"wayrestverify"};}
    public override string getDescription(){return "Check loaded Wayrest definition, prefab blocks, workstation tile entities and steward.";}
    public override void Execute(List<string> args,CommandSenderInfo sender) {
        try {
            if(QuestClass.GetQuest("delveWayrestSupplies")==null)throw new Exception("Missing supply quest");
            int id=EntityClass.FromString("delveWayrestSteward");
            if(EntityClass.GetEntityClassName(id)!="delveWayrestSteward")throw new Exception("Missing steward definition");
            World world=GameManager.Instance.World;
            int count=0;foreach(EntityAlive e in world.EntityAlives)if(e.entityClass==id){
                count++;SdtdConsole.Instance.Output("[Wayrest] steward "+Localization.Get(e.EntityName)+" at "+e.position);
                EntityTrader trader=e as EntityTrader;
                if(trader==null||trader.TraderData==null)throw new Exception("Steward trading data unavailable");
            }
            var poi=world.GetPOIAtPosition(new UnityEngine.Vector3(-2681,65,-2133),null,null);
            if(poi==null||poi.prefab==null||!poi.prefab.bTraderArea)throw new Exception("Wayrest is not a native trader area");
            SdtdConsole.Instance.Output("[Wayrest] live stewards="+count);
            int[,] points={{9,2,38},{14,2,38},{45,2,38},{30,2,27}};
            string[] names={"forge","workbench","cntWoodenChestClosed","campfire"};
            for(int i=0;i<4;i++){
                Vector3i pos=new Vector3i(-2711+points[i,0],63+points[i,1],-2182+points[i,2]);
                string actual=world.GetBlock(pos.x,pos.y,pos.z).Block.GetBlockName();
                TileEntity tile=world.GetTileEntity(pos);
                SdtdConsole.Instance.Output("[Wayrest] "+names[i]+" actual="+actual+" tile="+(tile==null?"NULL":tile.GetType().Name));
                if(actual!=names[i]||tile==null)throw new Exception("Missing functional block "+names[i]);
            }
            if(count!=1)throw new Exception("Expected exactly one live steward in loaded settlement");
            SdtdConsole.Instance.Output("[Wayrest] PASS quest, steward and four functional block tile entities");
        }catch(Exception ex){SdtdConsole.Instance.Output("[Wayrest] ERROR "+ex.Message);}
    }
}
