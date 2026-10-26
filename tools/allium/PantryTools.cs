using System;
using System.IO;
using System.Xml;
using System.Collections.Generic;
using UnityEngine;

public class ConsoleCmdPantry : ConsoleCmdAbstract
{
    static ChunkManager.ChunkObserver observer;
    public override string[] getCommands(){return new[]{"pantry"};}
    public override string getDescription(){return "pantry build|verify: isolated forest pantry authoring and verification.";}
    static void Check(bool value,string reason){if(!value)throw new Exception(reason);}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        try {
            if(args.Count>0 && args[0]=="load") {
                if(observer!=null)GameManager.Instance.RemoveChunkObserver(observer);
                observer=GameManager.Instance.AddChunkObserver(new Vector3(int.Parse(args[1]),80,int.Parse(args[2])),false,4,4);
                SdtdConsole.Instance.Output("[Pantry] Loading garden chunks.");return;
            }
            if(args.Count>0 && args[0]=="garden") {
                var gardenDoc=new XmlDocument();gardenDoc.Load(Path.Combine(ModManager.GetMod("AlliumTools",true).Path,"pantry-world-cells.xml"));
                var world=GameManager.Instance.World;int gardenCount=0;
                foreach(XmlElement cell in gardenDoc.SelectNodes("/gardens/garden[@name='"+args[1]+"']/cell")) {
                    int x=int.Parse(cell.GetAttribute("x")),y=int.Parse(cell.GetAttribute("y")),z=int.Parse(cell.GetAttribute("z"));
                    Check(world.GetBlock(x,y,z).Block.GetBlockName()=="delveFarmPlotPlate","Missing plate at "+x+","+y+","+z+" actual="+world.GetBlock(x,y,z).Block.GetBlockName());
                    Check(world.GetBlock(x,y+1,z).Block.GetBlockName()==cell.GetAttribute("crop"),"Missing crop at "+x+","+(y+1)+","+z);gardenCount++;
                }
                Check(gardenCount==12,"Expected 12 garden cells");SdtdConsole.Instance.Output("[Pantry] PASS world garden "+args[1]+": 12 plates and 12 ripe crops.");return;
            }
            if(args.Count>0 && args[0]=="wild") {
                int cx=int.Parse(args[1]),cz=int.Parse(args[2]);var world=GameManager.Instance.World;var counts=new SortedDictionary<string,int>();
                for(int z=cz-40;z<=cz+40;z++)for(int x=cx-40;x<=cx+40;x++) {
                    int height=world.GetTerrainHeight(x,z);
                    for(int y=Math.Max(1,height-1);y<=height+4;y++) {
                        string n=world.GetBlock(x,y,z).Block.GetBlockName();if(!n.StartsWith("planted"))continue;
                        if(!counts.ContainsKey(n))counts[n]=0;counts[n]++;
                    }
                }
                Check(counts.Count>0,"No wild crops found in sampled chunks");
                foreach(var pair in counts)SdtdConsole.Instance.Output("[Pantry] Wild "+pair.Key+"="+pair.Value);
                return;
            }
            if(args.Count>0 && args[0]=="build"){Build();return;}
            var doc=new XmlDocument();doc.Load(Path.Combine(ModManager.GetMod("AlliumTools",true).Path,"pantry-checks.xml"));
            int count=0;
            foreach(XmlElement row in doc.SelectNodes("/checks/recipe")) {
                string n=row.GetAttribute("name");var r=CraftingManager.GetRecipe(n);
                Check(r!=null,"Missing recipe "+n);
                Check(r.count==int.Parse(row.GetAttribute("count")),"Wrong batch "+n);
                Check(Delve.RecipeProgression.Minimum(n)==int.Parse(row.GetAttribute("rank")),"Wrong gate "+n);
                Check(Delve.TrainingHooks.CraftedSkill(n,r.craftingArea)==row.GetAttribute("skill"),"Wrong owner "+n);
                Check(ItemClass.GetItem(n,false).ItemClass!=null,"Missing output "+n);count++;
            }
            foreach(string key in new[]{"Bramble","Yarrow","Thyme","Mooncap"}) {
                string stem="plantedDelve"+key;
                foreach(string s in new[]{"1","2","3Harvest","3HarvestPlayer"})Check(!Block.GetBlockValue(stem+s,false).isair,"Missing plant "+stem+s);
                Check(Block.GetBlockValue(stem+"1",false).Block is BlockPlantGrowing,"Seed is not growing "+stem);
                Check(Block.GetBlockValue(stem+"2",false).Block is BlockPlantGrowing,"Sprout is not growing "+stem);
            }
            EntityAlive fixture=null;
            try {
                fixture=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),Vector3.zero) as EntityAlive;
                Check(fixture!=null,"Create consumable fixture");fixture.world=GameManager.Instance.World;
                fixture.Health=fixture.GetMaxHealth()-50;int before=fixture.Health;
                var heal=ItemClass.GetItem("delveLesserHealingPotion",false);
                heal.ItemClass.FireEvent(MinEventTypes.onSelfPrimaryActionEnd,new MinEventParams{Self=fixture,ItemValue=heal});
                Check(fixture.Health==before+25,"Healing potion actual restoration");
                Check(fixture.Buffs.HasBuff("delveRestorativeCooldown"),"Healing cooldown not applied");
                fixture.Stamina=fixture.GetMaxStamina()-60;float staminaBefore=fixture.Stamina;
                var stamina=ItemClass.GetItem("delveLesserStaminaPotion",false);
                stamina.ItemClass.FireEvent(MinEventTypes.onSelfPrimaryActionEnd,new MinEventParams{Self=fixture,ItemValue=stamina});
                Check(Math.Abs(fixture.Stamina-staminaBefore-40)<.01f,"Stamina potion actual restoration");
                var dressing=ItemClass.GetItem("medicalDelveHerbalDressing",false);
                dressing.ItemClass.FireEvent(MinEventTypes.onSelfPrimaryActionEnd,new MinEventParams{Self=fixture,ItemValue=dressing});
                Check(fixture.Buffs.GetCustomVar("medicalRegHealthAmount")==35,"Dressing recovery amount");
                var meal=ItemClass.GetItem("foodDelveHunterStew",false);
                meal.ItemClass.FireEvent(MinEventTypes.onSelfPrimaryActionEnd,new MinEventParams{Self=fixture,ItemValue=meal});
                Check(fixture.Buffs.GetCustomVar("$foodAmountAdd")==35,"Stew food amount");
            } finally {if(fixture!=null)UnityEngine.Object.Destroy(fixture.gameObject);}
            SdtdConsole.Instance.Output("[Pantry] PASS "+count+" recipe outputs, batches, skill gates and ownership; 16 plant stages; potion, dressing and meal engine effects.");
        }catch(Exception ex){SdtdConsole.Instance.Output("[Pantry] FAIL "+ex);}
    }
    static void Build()
    {
        string[] sources={"delve_forest_cabin_01","delve_forest_cabin_04","delve_forest_farm_12"};
        string[] crops={"plantedDelveBramble3HarvestPlayer","plantedDelveYarrow3HarvestPlayer","plantedDelveThyme3HarvestPlayer","plantedDelveMooncap3HarvestPlayer","plantedCorn3HarvestPlayer","plantedPotato3HarvestPlayer","plantedPumpkin3HarvestPlayer","plantedMushroom3HarvestPlayer","plantedCotton3HarvestPlayer","plantedChrysanthemum3HarvestPlayer","plantedGoldenrod3HarvestPlayer","plantedBlueberry3HarvestPlayer"};
        var report=new XmlDocument();report.LoadXml("<gardens/>");
        var plate=Block.GetBlockValue("delveFarmPlotPlate",false);Check(!plate.isair,"Missing plate");
        // Rest a horizontal plate on intact terrain, not at the top of an empty cell.
        bool found=false;float top=0,bottom=float.MaxValue;byte selected=0;
        for(byte rot=0;rot<24;rot++) {
            plate.rotation=rot;var boxes=plate.Block.shape.GetBounds(plate);
            if(boxes==null||boxes.Length==0)continue;
            Bounds b=boxes[0];foreach(var box in boxes)b.Encapsulate(box);
            if(b.size.y<.3f && b.size.x>.8f && b.size.z>.8f && b.min.y<bottom){bottom=b.min.y;top=b.max.y;selected=rot;found=true;}
        }
        Check(found,"No flat plate rotation");plate.rotation=selected;
        foreach(string source in sources) {
            Prefab original=new Prefab(),p=new Prefab();Check(original.Load(source,true,true,false,false),"Load "+source);Check(p.Load(source,true,true,false,false),"Reload source");
            var positions=new List<Vector3i>();
            // Choose one clear 3x4 garden on existing outdoor terrain, inset from borders.
            for(int z=3;z<p.size.z-7 && positions.Count==0;z++)for(int x=3;x<p.size.x-6 && positions.Count==0;x++)for(int y=0;y<p.size.y-4 && positions.Count==0;y++) {
                bool valid=true;
                for(int dz=-1;dz<=4 && valid;dz++)for(int dx=-1;dx<=3 && valid;dx++) {
                    var b=p.GetBlock(x+dx,y,z+dz);string n=b.Block.GetBlockName();
                    if(b.isair||b.ischild||!(n=="terrDirt"||n=="terrForestGround"||n=="terrGrass"||n=="terrainFiller")){valid=false;break;}
                    for(int yy=y+1;yy<p.size.y;yy++)if(!p.GetBlock(x+dx,yy,z+dz).isair){valid=false;break;}
                }
                if(valid)for(int dz=0;dz<4;dz++)for(int dx=0;dx<3;dx++)positions.Add(new Vector3i(x+dx,y+1,z+dz));
            }
            Check(positions.Count==12,"No safe outdoor garden in "+source);
            var changed=new HashSet<Vector3i>();
            for(int i=0;i<positions.Count;i++) {
                var pos=positions[i];p.SetBlock(pos.x,pos.y,pos.z,plate);p.SetDensity(pos.x,pos.y,pos.z,127);p.SetTexture(pos.x,pos.y,pos.z,TextureFullArray.Default);changed.Add(pos);
                var crop=Block.GetBlockValue(crops[i],false);Check(!crop.isair,"Missing crop "+crops[i]);
                p.SetBlock(pos.x,pos.y+1,pos.z,crop);changed.Add(pos+new Vector3i(0,1,0));changed.Add(pos+new Vector3i(0,2,0));changed.Add(pos+new Vector3i(0,3,0));
            }
            p.AddAllChildBlocks();p.bExcludeDistantPOIMesh=true;
            string dest=source+"_garden";
            var loc=PathAbstractions.PrefabsSearchPaths.BuildLocation((PathAbstractions.EAbstractedLocationType)3,"POIs",dest,ModManager.GetMod("DelveWayrest",true),null).Value;
            Check(p.Save(loc,true),"Save garden");p.AddAllChildBlocks();
            var meta=new XmlDocument();meta.Load(original.location.FullPathNoExtension+".xml");meta.Save(loc.FullPathNoExtension+".xml");
            Prefab check=new Prefab();Check(check.Load(loc,true,true,false,false),"Reload garden");
            for(int y=0;y<p.size.y;y++)for(int z=0;z<p.size.z;z++)for(int x=0;x<p.size.x;x++) {
                var pos=new Vector3i(x,y,z);
                Check(p.GetBlock(x,y,z).rawData==check.GetBlock(x,y,z).rawData,"Serialization "+pos);
                if(!changed.Contains(pos))Check(original.GetBlock(x,y,z).rawData==check.GetBlock(x,y,z).rawData,"Changed outside garden "+pos);
            }
            var row=report.CreateElement("garden");row.SetAttribute("source",source);row.SetAttribute("target",dest);row.SetAttribute("rotation",selected.ToString());row.SetAttribute("top",top.ToString(System.Globalization.CultureInfo.InvariantCulture));
            for(int i=0;i<positions.Count;i++) {var cell=report.CreateElement("cell");cell.SetAttribute("x",positions[i].x.ToString());cell.SetAttribute("y",positions[i].y.ToString());cell.SetAttribute("z",positions[i].z.ToString());cell.SetAttribute("crop",crops[i]);row.AppendChild(cell);}
            report.DocumentElement.AppendChild(row);
            report.Save(Path.Combine(ModManager.GetMod("AlliumTools",true).Path,"pantry-gardens.xml"));
            SdtdConsole.Instance.Output("[Pantry] PASS garden "+dest+" 12 planted plates; all other blocks preserved; rotation="+selected);
        }
    }
}



