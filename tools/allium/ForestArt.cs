using System;
using System.IO;
using System.Collections.Generic;
using System.Xml;

public class ConsoleCmdForestArt : ConsoleCmdAbstract
{
    static readonly string[] Sources={"delve_wayrest_01","cabin_01","cabin_04","cemetery_01","cabin_05","cabin_06","cabin_07","cabin_08","cabin_10","cabin_12","cabin_14","farm_12","oldwest_business_01","oldwest_business_08","oldwest_church","ranger_station_05"};
    public override string[] getCommands(){return new[]{"forestart"};}
    public override string getDescription(){return "Development-only Forest prefab inventory / art conversion.";}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        try {
            string output=Path.Combine(ModManager.GetMod("AlliumTools",true).Path,"forest-inventory.tsv");
            if(args.Count>0 && args[0]=="build") { Build(); return; }
            using(var writer=new StreamWriter(output)) {
                writer.WriteLine("prefab\tblock\tcount");
                foreach(string name in Sources) {
                    Prefab p=new Prefab();if(!p.Load(name,true,true,false,false))throw new Exception("Cannot load "+name);
                    var counts=new SortedDictionary<string,int>();
                    for(int y=0;y<p.size.y;y++)for(int z=0;z<p.size.z;z++)for(int x=0;x<p.size.x;x++) {
                        BlockValue b=p.GetBlock(x,y,z);if(b.isair||b.ischild)continue;
                        string key=b.Block.GetBlockName();if(!counts.ContainsKey(key))counts[key]=0;counts[key]++;
                    }
                    foreach(var pair in counts)writer.WriteLine(name+"\t"+pair.Key+"\t"+pair.Value);
                }
            }
            SdtdConsole.Instance.Output("[ForestArt] Inventory saved "+output);
        }catch(Exception ex){SdtdConsole.Instance.Output("[ForestArt] FAIL "+ex);}
    }

    static TextureFullArray Paint(int side,int top)
    {
        long packed=0;for(int face=0;face<6;face++)packed|=((long)(face==(int)BlockFace.Top?top:side))<<(face*8);
        return new TextureFullArray(packed);
    }
    static string Replacement(string n)
    {
        string s=n.ToLowerInvariant();
        // Quest actors, reset/fetch markers, switches, traps, and hero rewards
        // are deliberately left intact. These contain gameplay data.
        if(s.Contains("quest")||s.Contains("sleeper")||s.Contains("trap")||s.Contains("hero")||s.Contains("safe")||s.Contains("keyrack"))return null;
        if(s.StartsWith("cnt")) {
            if(s.Contains("fridge")||s.Contains("cooler")||s.Contains("microwave")||s.Contains("toaster")||s.Contains("coffeemaker")||s.Contains("stove")||s.Contains("grill"))return "cntFoodPileSmall";
            if(s.Contains("washer")||s.Contains("dryer")||s.Contains("laundry")||s.Contains("luggage")||s.Contains("sportsbag"))return "cntWoodenChestRottenClosed";
            if(s.Contains("toilet")||s.Contains("bathtub")||s.Contains("trash")||s.Contains("watercooler"))return "cntOldWestChestRandomLootHelper";
            if(s.Contains("filecabinet")||s.Contains("deskmetal")||s.Contains("cashregister")||s.Contains("mailbox")||s.Contains("rollingtool")||s.Contains("toolbox"))return "cntWoodenChestRottenClosed";
            if(s.Contains("medicinecabinet")||s.Contains("pillcase"))return "cntMedicLootPileA";
            if(s.Contains("casketmodern"))return "cntCoffinWildWestClosed";
            if(s.Contains("pickuptruck"))return "cntWoodenChestRottenClosed";
            if(s.Contains("barrel"))return "cntOldWestChestRandomLootHelper";
            if(s.Contains("solar")||s.Contains("electronics"))return "cntWoodenChestRottenClosed";
        }
        if(s.StartsWith("chaircamping")||s.StartsWith("chairfolding")||s.StartsWith("officechair"))return "chairWood01";
        if(s.StartsWith("couch")||s.StartsWith("sectional"))return "woodShapes:table";
        if(s.StartsWith("bed02")||s.StartsWith("bunkbed")||s.StartsWith("mattress"))return "bedrollPOI";
        if(s.StartsWith("bodybag"))return "goreBlockHumanBones";
        if(s.StartsWith("cars")||s.StartsWith("carwreck")||s=="tractorgreen"||s.StartsWith("decocar")||s=="tablesaw")return "woodShapes:storageCubeHalf";
        if(s.StartsWith("waterheater")||s.StartsWith("tankpropane")||s=="portapottybrown")return "wineBarrelPlain";
        if(s.StartsWith("tablelamp")||s.StartsWith("desklamp")||s.StartsWith("endtablelamp")||s.StartsWith("flashlight"))return "candleTableLight";
        if(s.StartsWith("lightwall")||s.StartsWith("lightporch")||s.StartsWith("lightsconce")||s=="lightindustrialmountedwall")return "candleWallLight";
        if(s.StartsWith("ceiling")||s.StartsWith("lightceiling")||s.StartsWith("lightindustrial")||s.StartsWith("industriallight")||s.StartsWith("spotlight")||s=="worklightpoi")return "air";
        if(s.StartsWith("breakerbox")||s.StartsWith("commercialdistribution")||s.StartsWith("residentialsingle")||s.StartsWith("conduit")||s.StartsWith("pipesmall")||s.StartsWith("metalpipe")||s.StartsWith("satellite")||s=="radioham"||s.StartsWith("tv")||s=="decolaptop"||s.StartsWith("shower")||s.Contains("sink")||s=="hoodrangewhite")return "air";
        if(s.StartsWith("poster")||s.StartsWith("calendar")||s.StartsWith("signposter")||s.StartsWith("signmisc")||s.StartsWith("signyard")||s.StartsWith("newspaper")||s.StartsWith("wallclock")||s.StartsWith("signdecal")||s.StartsWith("signcanvas"))return "air";
        if(s.StartsWith("chainlink") && !s.Contains("door"))return "woodShapes:plate";
        if(s=="chainlinkfencedoor")return "woodenFenceDoorBrown";
        if(s.StartsWith("barbedwire"))return "woodShapes:trellisDiamond";
        if(s.StartsWith("cinderblocks")||s.StartsWith("rubblepilecement")||s.StartsWith("rubblepileconcrete"))return "resourceRock01";
        return null;
    }
    static void Build()
    {
        Mod mod=ModManager.GetMod("DelveWayrest",true),tools=ModManager.GetMod("AlliumTools",true);
        string reportPath=Path.Combine(tools.Path,"forest-art-report.xml");
        if(File.Exists(reportPath))File.Delete(reportPath);
        var report=new XmlDocument();report.LoadXml("<forestArt/> ");
        foreach(string name in Sources) {
            Prefab original=new Prefab();if(!original.Load(name,true,true,false,false))throw new Exception("Cannot load "+name);
            // Load a separate editable instance, retaining original as comparison data.
            Prefab p=new Prefab();if(!p.Load(name,true,true,false,false))throw new Exception("Cannot reload "+name);
            if(name=="delve_wayrest_01") {
                SdtdConsole.Instance.Output("[ForestArt] Wayrest original cell="+original.GetBlock(10,2,12).Block.GetBlockName()+" editable cell="+p.GetBlock(10,2,12).Block.GetBlockName());
            }
            var replacements=new Dictionary<Vector3i,BlockValue>();int painted=0,removedChildren=0,addedLights=0;
            for(int y=0;y<p.size.y;y++)for(int z=0;z<p.size.z;z++)for(int x=0;x<p.size.x;x++) {
                BlockValue b=original.GetBlock(x,y,z);if(b.isair||b.ischild)continue;
                string old=b.Block.GetBlockName(),replacement=Replacement(old);
                if(replacement!=null && !original.triggerData.ContainsKey(new Vector3i(x,y,z))) {
                    BlockValue v=Block.GetBlockValue(replacement,false);
                    if(v.isair && replacement!="air")throw new Exception("Missing native replacement "+replacement);
                    // Only one-cell props or identical native multiblock extents.
                    // Door rotations and metadata are retained, all other props
                    // use their canonical upright orientation.
                    if(v.Block.isMultiBlock && (!b.Block.isMultiBlock || v.Block.multiBlockPos.dim!=b.Block.multiBlockPos.dim))
                        v=Block.GetBlockValue("cntWoodenChestRottenClosed",false);
                    if(old.ToLowerInvariant().Contains("door")||replacement=="candleWallLight"||replacement.Contains(":plate"))v.rotation=b.rotation;
                    replacements.Add(new Vector3i(x,y,z),v);
                }
                if(old.Contains("Shapes:") && !old.StartsWith("glass") && !old.StartsWith("awning")) {
                    string shape=old.Substring(old.IndexOf(':')+1).ToLowerInvariant();
                    bool wood=old.StartsWith("wood"),roof=shape.Contains("wedge")||shape.Contains("slope")||shape=="ramp";
                    int side=wood?67:63,top=wood?59:63;
                    if(wood && roof && y>p.size.y/3){side=17;top=17;}
                    else if(wood && shape=="cube" && y>2 && x%5!=0 && z%5!=0){side=68;}
                    if(name=="delve_wayrest_01" && wood && y>=7){side=17;top=17;}
                    // Native paint IDs, six packed 8-bit face indices.
                    p.SetTexture(x,y,z,Paint(side,top));painted++;
                }
            }
            // Remove only children belonging to replaced parents, leaving every
            // unrelated multiblock and its native metadata unchanged.
            for(int y=0;y<p.size.y;y++)for(int z=0;z<p.size.z;z++)for(int x=0;x<p.size.x;x++) {
                var b=original.GetBlock(x,y,z);if(!b.ischild)continue;
                if(replacements.ContainsKey(new Vector3i(x+b.parentx,y+b.parenty,z+b.parentz))){p.SetBlock(x,y,z,BlockValue.Air);p.SetTexture(x,y,z,TextureFullArray.Default);removedChildren++;}
            }
            foreach(var change in replacements){var pos=change.Key;p.tileEntities.Remove(pos);p.SetBlock(pos.x,pos.y,pos.z,change.Value);p.SetTexture(pos.x,pos.y,pos.z,TextureFullArray.Default);}
            if(name=="delve_wayrest_01") {
                // Furnish the existing shelters without narrowing their doorways,
                // service approaches, or the main north/south circulation lane.
                Place(p,10,2,12,"woodShapes:table");Place(p,16,2,12,"woodShapes:table");
                Place(p,10,2,13,"chairWood01");Place(p,16,2,13,"chairWood01");
                Place(p,19,2,19,"wineBarrelPlain");Place(p,45,2,33,"wineBarrelPlain");
                Place(p,51,2,33,"wineBarrelPlain");
                Place(p,24,2,44,"chairWood01");Place(p,37,2,44,"chairWood01");
            }
            // Candles on existing tables replace electrical ambient lighting
            // without blocking floor routes or attaching to unsupported air.
            for(int y=1;y<p.size.y-2;y++)for(int z=1;z<p.size.z-1;z++)for(int x=1;x<p.size.x-1;x++) {
                var b=p.GetBlock(x,y,z);if(b.isair||b.ischild)continue;
                string n=b.Block.GetBlockName();
                if((n=="woodShapes:table"||n=="diningTable01"||n=="tableCommunion") && p.GetBlock(x,y+1,z).isair && addedLights<12)
                {p.SetBlock(x,y+1,z,Block.GetBlockValue("candleTableLight",false));addedLights++;}
            }
            p.AddAllChildBlocks();p.bExcludeDistantPOIMesh=true;
            foreach(var change in replacements) {
                var pos=change.Key;
                if(p.GetBlock(pos.x,pos.y,pos.z).rawData!=change.Value.rawData)
                    throw new Exception("Replacement did not land at "+pos);
            }
            string dest=name=="delve_wayrest_01"?"delve_wayrest_forest":"delve_forest_"+name;
            var loc=PathAbstractions.PrefabsSearchPaths.BuildLocation((PathAbstractions.EAbstractedLocationType)3,"POIs",dest,mod,null).Value;
            Directory.CreateDirectory(Path.GetDirectoryName(loc.FullPath));if(!p.Save(loc,true))throw new Exception("Save failed "+dest);
            // Save strips generated child cells from this instance. Restore them
            // before comparing with Load(..., fixChildBlocks:true), which does likewise.
            p.AddAllChildBlocks();
            // Preserve all source encounter volumes, indexed markers, triggers,
            // quest eligibility and height offset exactly. Only LOD/editor tags
            // change; native distant meshes would display the old appearance.
            var xml=new XmlDocument();xml.Load(original.location.FullPathNoExtension+".xml");
            Set(xml,"ExcludeDistantPOIMesh","True");Set(xml,"EditorGroups","Delve Forest");
            xml.Save(loc.FullPathNoExtension+".xml");
            Prefab check=new Prefab();if(!check.Load(loc,true,true,false,false))throw new Exception("Reload failed");
            int checkedBlocks=0;
            for(int y=0;y<p.size.y;y++)for(int z=0;z<p.size.z;z++)for(int x=0;x<p.size.x;x++) {
                var v=p.GetBlock(x,y,z);var re=check.GetBlock(x,y,z);
                if(v.rawData!=re.rawData || p.GetTexture(x,y,z)!=check.GetTexture(x,y,z))throw new Exception("Serialization mismatch "+dest+" "+x+","+y+","+z+" before="+v.rawData+"/"+v.Block.GetBlockName()+" child="+v.ischild+" after="+re.rawData+"/"+re.Block.GetBlockName()+" child="+re.ischild+" textureEqual="+(p.GetTexture(x,y,z)==check.GetTexture(x,y,z)));
                string n=original.GetBlock(x,y,z).Block.GetBlockName().ToLowerInvariant();
                if((n.Contains("sleeper")||n.Contains("quest")||n.Contains("trap")||n.Contains("hero")||n.Contains("keyrack")) && original.GetBlock(x,y,z).rawData!=re.rawData)throw new Exception("Gameplay marker changed "+n);
                checkedBlocks++;
            }
            var entry=report.CreateElement("prefab");entry.SetAttribute("source",name);entry.SetAttribute("target",dest);entry.SetAttribute("painted",painted.ToString());entry.SetAttribute("replaced",replacements.Count.ToString());entry.SetAttribute("removedChildren",removedChildren.ToString());entry.SetAttribute("tableCandles",addedLights.ToString());entry.SetAttribute("verifiedCells",checkedBlocks.ToString());report.DocumentElement.AppendChild(entry);
            SdtdConsole.Instance.Output("[ForestArt] PASS "+dest+" paint="+painted+" replace="+replacements.Count+" candles="+addedLights);
        }
        report.Save(reportPath);
    }
    static void Set(XmlDocument doc,string name,string value) {
        var e=doc.SelectSingleNode("/prefab/property[@name='"+name+"']") as XmlElement;
        if(e==null){e=doc.CreateElement("property");e.SetAttribute("name",name);doc.DocumentElement.AppendChild(e);}e.SetAttribute("value",value);
    }
    static void Place(Prefab p,int x,int y,int z,string name) {
        if(!p.GetBlock(x,y,z).isair||p.GetBlock(x,y-1,z).isair)throw new Exception("Invalid furniture site "+name+" at "+x+","+y+","+z+" cell="+p.GetBlock(x,y,z).Block.GetBlockName()+" floor="+p.GetBlock(x,y-1,z).Block.GetBlockName());
        var b=Block.GetBlockValue(name,false);
        if(b.isair||b.Block.isMultiBlock)throw new Exception("Furniture must be native single-cell "+name);
        p.SetBlock(x,y,z,b);
        if(name.StartsWith("woodShapes:"))p.SetTexture(x,y,z,Paint(67,59));
    }
}
