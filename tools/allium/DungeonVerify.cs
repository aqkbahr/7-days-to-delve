using System;
using System.IO;
using System.Xml;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;

public class ConsoleCmdDungeonVerify:ConsoleCmdAbstract
{
    static ChunkManager.ChunkObserver observer;
    static EntityPlayer lightingPlayer;
    static void Emit(string s){Log.Out(s);SdtdConsole.Instance.Output(s);}
    public override string[] getCommands(){return new[]{"dungeoncheck"};}
    public override string getDescription(){return "Developer dungeon registry, load/check/reset <index>, and board fixtures.";}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        EntityPlayer player=null;
        try {
            var w=GameManager.Instance.World;
            if(args[0]=="unload"){
                if(observer!=null){GameManager.Instance.RemoveChunkObserver(observer);observer=null;}
                if(lightingPlayer!=null){w.Players.Remove(lightingPlayer.entityId);w.Entities.Remove(lightingPlayer.entityId);UnityEngine.Object.Destroy(lightingPlayer.gameObject);lightingPlayer=null;}
                Emit("[Dungeons] PASS unloaded diagnostic observer and player");return;
            }
            if(args[0]=="flora"){
                foreach(string floraName in new[]{"plantedMushroom3Harvest","plantedDelveMooncap3Harvest"})
                    if(!NonblockingFlora(Block.GetBlockValue(floraName,false).Block))throw new Exception("Mature mushroom is not recognized nonblocking flora: "+floraName);
                if(NonblockingFlora(Block.GetBlockValue("cobblestoneShapes:cube",false).Block))throw new Exception("Solid masonry misclassified as flora");
                Emit("[Dungeons] PASS flora: native mushroom and Mooncap are nonblocking mature decorations; masonry remains an obstruction.");return;
            }
            if(args[0]=="registry"){
                int[] counts={0,0,0};
                for(int tier=1;tier<=2;tier++)foreach(var p in QuestEventManager.Current.GetPrefabsByDifficultyTier(tier))
                    if(p.name.StartsWith("delve_dungeon_")){
                        if(w.GetBiomeInWorld(p.boundingBoxPosition.x,p.boundingBoxPosition.z).m_sBiomeName!="pine_forest")throw new Exception("Wrong biome");
                        if(!p.prefab.SleeperVolumeList.AnyUsedEntry || !p.prefab.indexedBlockOffsets.ContainsKey("Rally") || !p.prefab.indexedBlockOffsets.ContainsKey("FetchContainer"))throw new Exception("Missing native quest data");
                        if(p.prefab.bTraderArea||!p.prefab.bCopyAirBlocks||p.prefab.yOffset>=0)throw new Exception("Wrong underground/digging configuration");
                        counts[tier]++;
                    }
                if(counts[1]!=2||counts[2]!=2)throw new Exception("Expected two delves per tier");
                Emit("[Dungeons] PASS registry: two Tier 1 and two Tier 2 Forest delves; native clear/fetch markers, encounters and ordinary destructible space.");return;
            }
            if(args[0]=="board"){
                EntityTrader trader=null;foreach(var e in w.EntityAlives)if(EntityClass.GetEntityClassName(e.entityClass)=="delveWayrestSteward")trader=e as EntityTrader;
                if(trader==null)throw new Exception("Load Wayrest first");trader.OnUpdateLive();
                player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),trader.position) as EntityPlayer;player.world=w;
                var locked=new HashSet<string>();var unlocked=new HashSet<string>();var kinds=new HashSet<string>();var variants=new Dictionary<string,HashSet<string>>();int offers=0;
                for(int phase=0;phase<=1;phase++){
                    player.Buffs.SetCustomVar("delveWayrestReady",phase,false);
                    for(int run=0;run<35;run++)foreach(var q in trader.PopulateActiveQuests(player,6,0)){
                        if(q.ID.Contains("onward"))continue;
                        int tier=q.QuestClass.DifficultyTier;
                        if(phase==0 && tier!=1)throw new Exception("Tier 2 unlocked before milestone");
                        Vector3 pos=q.GetLocation();if(w.GetBiomeInWorld((int)pos.x,(int)pos.z).m_sBiomeName!="pine_forest")throw new Exception("Board biome leak");
                        var poi=w.GetPOIAtPosition(pos+q.GetLocationSize()/2,null,null);
                        if(poi!=null&&poi.name.StartsWith("delve_dungeon_")){
                            if(phase==0)locked.Add(poi.prefab.PrefabName);else unlocked.Add(poi.prefab.PrefabName);
                            if(tier==2)kinds.Add(q.ID);
                            if(!variants.ContainsKey(poi.prefab.PrefabName))variants[poi.prefab.PrefabName]=new HashSet<string>();
                            variants[poi.prefab.PrefabName].Add(q.ID);
                        }
                        offers++;
                    }
                }
                if(locked.Count!=2||unlocked.Count!=4||kinds.Count!=3)throw new Exception("Board coverage "+locked.Count+" / "+unlocked.Count+" / "+kinds.Count);
                foreach(var variant in variants)if(variant.Value.Count!=3)throw new Exception("Missing quest-type coverage for "+variant.Key);
                Emit("[Dungeons] PASS per-site offers: Fetch, Clear and Fetch/Clear selected for each of the four delves.");
                Emit("[Dungeons] PASS board: "+offers+" offers; both Tier 1 delves before milestone, all four afterward; three Tier 2 quest types; Forest only.");return;
            }
            var doc=new XmlDocument();doc.Load(Path.Combine(ModManager.GetMod("AlliumTools",true).Path,"dungeon-sites.xml"));
            var e2=(XmlElement)doc.DocumentElement.ChildNodes[int.Parse(args[1])];string name=e2.GetAttribute("name");
            int x=int.Parse(e2.GetAttribute("x")),ground=int.Parse(e2.GetAttribute("y")),z=int.Parse(e2.GetAttribute("z"));
            Prefab prefab=new Prefab();if(!prefab.Load(name,true,true,false,false))throw new Exception("Missing prefab");
            if(args[0]=="repairtorch"){RepairSmugglerTorch(prefab);return;}
            if(args[0]=="reinforce"){
                if(name!="delve_dungeon_cave_12")throw new Exception("Reinforcement is scoped to Old Warden");
                Reinforce(prefab);return;
            }
            if(args[0]=="load"){
                if(observer!=null)GameManager.Instance.RemoveChunkObserver(observer);
                // Native task_Lighting budgets work at Players.Count * 2. A
                // headless observer alone loads blocks but never initializes SI.
                // Register a test player so the ordinary scheduler runs; never
                // seed stability values or invoke the calculator directly.
                if(lightingPlayer==null){
                    lightingPlayer=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),new Vector3(x+12,250,z+12)) as EntityPlayer;
                    lightingPlayer.world=w;w.Players.Add(lightingPlayer.entityId,lightingPlayer);w.Entities.Add(lightingPlayer.entityId,lightingPlayer);
                }
                lightingPlayer.SetPosition(new Vector3(x+12,250,z+12));
                observer=GameManager.Instance.AddChunkObserver(new Vector3(x+prefab.size.x/2,ground,z+prefab.size.z/2),false,6,-1);
                Emit("[Dungeons] Requested "+name);return;
            }
            if(args[0]=="ready"){
                var stone=Block.GetBlockValue("terrStone",false).Block;
                Emit("[Dungeons] Stone stabilitySupport="+stone.StabilitySupport+" stabilityIgnore="+stone.StabilityIgnore);
                bool ready=true;
                for(int cz=z>>4;cz<=(z+prefab.size.z-1)>>4;cz++)for(int cx=x>>4;cx<=(x+prefab.size.x-1)>>4;cx++){
                    var chunk=w.GetChunkSync(cx,cz) as Chunk;
                    if(chunk==null){ready=false;Emit("[Dungeons] Pending chunk "+cx+","+cz);continue;}
                    bool complete=chunk.IsInitialized&&!chunk.NeedsLightCalculation&&!chunk.InProgressLighting&&!chunk.StopStabilityCalculation;
                    ready &= complete;
                    Emit("[Dungeons] Chunk "+cx+","+cz+" initialized="+chunk.IsInitialized+" needsLight="+chunk.NeedsLightCalculation+" lighting="+chunk.InProgressLighting+" stopStability="+chunk.StopStabilityCalculation+" needsDecoration="+chunk.NeedsDecoration+" decorating="+chunk.InProgressDecorating);
                }
                for(int cz=(z>>4)-1;cz<=((z+prefab.size.z-1)>>4)+1;cz++)for(int cx=(x>>4)-1;cx<=((x+prefab.size.x-1)>>4)+1;cx++){
                    var neighbor=w.GetChunkSync(cx,cz) as Chunk;
                    if(neighbor==null||neighbor.NeedsDecoration)Emit("[Dungeons] Neighbor pending "+cx+","+cz+" "+(neighbor==null?"missing":"decoration"));
                }
                Emit("[Dungeons] "+(ready?"PASS ready":"WAIT readiness")+" "+name);return;
            }
            if(args[0]=="restore"){
                var restorePoi=w.GetPOIAtPosition(new Vector3(x+prefab.size.x/2,ground+prefab.yOffset+prefab.size.y/2,z+prefab.size.z/2),null,null);
                var key=((Chunk)w.GetChunkSync(x>>4,z>>4)).Key;
                GameManager.Instance.StartCoroutine(Restore(w,restorePoi,key));return;
            }
            if(args[0]=="guardian"){
                var poi=w.GetPOIAtPosition(new Vector3(x+prefab.size.x/2,ground+prefab.yOffset+prefab.size.y/2,z+prefab.size.z/2),null,null);
                if(poi==null||poi.sleeperVolumes==null)throw new Exception("Load encounter volumes first");
                int index=name=="delve_dungeon_cave_11"?0:2;
                var volume=poi.sleeperVolumes[index];string enemy=name=="delve_dungeon_cave_06"||name=="delve_dungeon_cave_11"?"delveCorruptedWalker":"delvePossessedSoldier";
                var flags=BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;
                var reset=typeof(SleeperVolume).GetMethod("DespawnAndReset",flags);
                reset.Invoke(volume,new object[]{w});
                try{
                    var points=volume.GetSpawnPoints();int slot=-1;
                    int walk=EntityAlive.GetSpawnWalkType(EntityClass.list[EntityClass.FromString(enemy)]);
                    for(int n=0;n<points.Count;n++)if(!points[n].GetBlock().ExcludesWalkType(walk)){slot=n;break;}
                    if(slot<0)throw new Exception("No compatible guardian slot");
                    var before=new HashSet<int>();foreach(var entity in w.EntityAlives)before.Add(entity.entityId);
                    bool queued=(bool)typeof(SleeperVolume).GetMethod("Spawn",flags).Invoke(volume,new object[]{w,EntityClass.FromString("zombieBoe"),slot,points[slot].GetBlock()});
                    if(!queued)throw new Exception("Guardian spawn was rejected");
                    typeof(SleeperVolume).GetMethod("CompletePendingSpawns",flags).Invoke(volume,null);
                    bool found=false;foreach(var entity in w.EntityAlives)if(!before.Contains(entity.entityId)&&EntityClass.GetEntityClassName(entity.entityClass)==enemy)found=true;
                    if(!found)throw new Exception("Native sleeper spawn did not produce "+enemy);
                    Emit("[Dungeons] PASS guardian "+name+": native sleeper spawn produced "+enemy);
                }finally{reset.Invoke(volume,new object[]{w});}
                return;
            }
            if(args[0]=="diagnose"){
                if(w.GetChunkSync(x>>4,z>>4)==null||w.GetBlock(x,ground+prefab.yOffset,z).isair)throw new Exception("Diagnostic chunks/foundation are not ready");
                using(var output=new StreamWriter(Path.Combine(ModManager.GetMod("AlliumTools",true).Path,"dungeon-diagnostic.csv"))){
                    output.WriteLine("x,y,z,expected,actual,stability");
                    for(int yy=0;yy<prefab.size.y;yy++)for(int zz=0;zz<prefab.size.z;zz++)for(int xx=0;xx<prefab.size.x;xx++){
                        var pos=new Vector3i(x+xx,ground+prefab.yOffset+yy,z+zz);
                        output.WriteLine(xx+","+yy+","+zz+","+prefab.GetBlock(xx,yy,zz).Block.GetBlockName()+","+w.GetBlock(pos).Block.GetBlockName()+","+w.GetStability(pos));
                    }
                }
                Emit("[Dungeons] Diagnostic saved");return;
            }
            int air=0,paint=0,grass=0,rock=0;Vector3i sample=Vector3i.zero;
            var obstructions=new Dictionary<string,int>();
            for(int yy=1;yy<-prefab.yOffset-2;yy++)for(int zz=1;zz<prefab.size.z-1;zz++)for(int xx=1;xx<prefab.size.x-1;xx++){
                var expected=prefab.GetBlock(xx,yy,zz);var pos=new Vector3i(x+xx,ground+prefab.yOffset+yy,z+zz);
                if(w.GetChunkSync(pos.x>>4,pos.z>>4)==null)throw new Exception("Load chunks first");
                if(expected.isair&&!prefab.IsWater(xx,yy,zz)){
                    var actual=w.GetBlock(pos);
                    // Native terrain decoration can add nonblocking plants to
                    // cave floors. It is not uncarved terrain; count separately.
                    string actualName=actual.Block.GetBlockName();
                    // Mature model-based mushrooms are terrain-decoration crops,
                    // but do not use the native PlantGrowing class/IsPlant flag.
                    if(NonblockingFlora(actual.Block)){grass++;continue;}
                    if(!actual.isair){int count;obstructions.TryGetValue(actualName,out count);obstructions[actualName]=count+1;continue;}
                    air++;
                    // Test an ordinary floor placement, not the final air cell
                    // in the scan (which may hang from a cave ceiling).
                    var below=w.GetBlock(pos+new Vector3i(0,-1,0));
                    if(sample==Vector3i.zero&&!below.isair&&below.Block.IsCollideMovement)sample=pos;
                }
                else if(expected.Block.GetBlockName().Contains("Shapes:")&&!expected.ischild&&paint<40){
                    if(w.GetBlock(pos).type!=expected.type||w.GetTextureFullArray(pos.x,pos.y,pos.z)!=prefab.GetTexture(xx,yy,zz))throw new Exception("Structure/paint mismatch");paint++;
                }
                if(expected.Block.GetBlockName().StartsWith("terr")&&!expected.Block.GetBlockName().StartsWith("terrainFiller")&&prefab.GetDensity(xx,yy,zz)<0){
                    if(w.GetBlock(pos).isair)throw new Exception("Missing solid cave terrain at "+pos);
                    rock++;
                }
            }
            if(obstructions.Count>0){var details=new List<string>();foreach(var pair in obstructions)details.Add(pair.Key+"="+pair.Value);throw new Exception("Underground obstructions: "+string.Join(", ",details.ToArray()));}
            if(air<100)throw new Exception("Too little carved space");
            if(args[0]=="stress"){
                bool ceiling=args.Count>2&&args[2]=="ceiling";
                if(ceiling){if(name!="delve_dungeon_cave_12")throw new Exception("Ceiling regression is specific to Old Warden");sample=new Vector3i(x+20,ground+prefab.yOffset+22,z+21);}
                if(sample==Vector3i.zero||!w.GetBlock(sample).isair)throw new Exception("Invalid stress test cell");
                var structure=new Dictionary<Vector3i,BlockValue>();
                for(int yy=0;yy<prefab.size.y;yy++)for(int zz=0;zz<prefab.size.z;zz++)for(int xx=0;xx<prefab.size.x;xx++){
                    var pos=new Vector3i(x+xx,ground+prefab.yOffset+yy,z+zz);var block=w.GetBlock(pos);string blockName=block.Block.GetBlockName();
                    if(blockName.StartsWith("terr")||blockName.Contains("Shapes:"))structure[pos]=block;
                }
                if(structure.Count<100)throw new Exception("Structure has not loaded");
                GameManager.Instance.StartCoroutine(Stress(w,name,sample,structure,ceiling));return;
            }
            if(args[0]=="reset"){
                if(sample==Vector3i.zero)throw new Exception("No supported floor placement for reset fixture");
                var poi=w.GetPOIAtPosition(new Vector3(x+prefab.size.x/2,ground+prefab.yOffset+prefab.size.y/2,z+prefab.size.z/2),null,null);
                if(poi==null)throw new Exception("Missing placed POI");
                Emit("[Dungeons] Reset floor sample "+sample+" support="+w.GetBlock(sample+new Vector3i(0,-1,0)).Block.GetBlockName()+" stability="+w.GetStability(sample+new Vector3i(0,-1,0)));
                w.SetBlocksRPC(new List<BlockChangeInfo>{new BlockChangeInfo(new BlockValueRef(sample),Block.GetBlockValue("woodShapes:cube",false))});
                long key=((Chunk)w.GetChunkSync(sample.x>>4,sample.z>>4)).Key;
                GameManager.Instance.StartCoroutine(Reset(w,poi,sample,key));Emit("[Dungeons] Reset fixture started "+name);return;
            }
            Emit("[Dungeons] PASS generated "+name+": "+air+" underground air cells, "+grass+" native nonblocking plant cells, "+rock+" solid terrain cells and "+paint+" structural paint samples.");
        }catch(Exception ex){Emit("[Dungeons] FAIL "+ex);}
        finally{if(player!=null)UnityEngine.Object.Destroy(player.gameObject);}
    }
    static bool NonblockingFlora(Block block){
        string name=block.GetBlockName();
        bool mushroom=block.IsTerrainDecoration && (name=="plantedMushroom3Harvest"||name=="plantedDelveMooncap3Harvest");
        return !block.IsCollideMovement && (block.IsPlant()||mushroom);
    }
    static IEnumerator Reset(World w,PrefabInstance poi,Vector3i sample,long key){
        yield return null;
        if(w.GetBlock(sample).type!=Block.GetBlockValue("woodShapes:cube",false).type){Emit("[Dungeons] FAIL reset fixture mutation was not applied");yield break;}
        var routine=poi.ResetBlocksAndRebuild(w,FastTags<TagGroup.Global>.Parse("clear,fetch"),key);
        while(routine.MoveNext())yield return routine.Current;
        yield return new WaitForSeconds(1);
        Emit(w.GetBlock(sample).isair?"[Dungeons] PASS native reset restored altered underground cell in "+poi.name:"[Dungeons] FAIL reset did not restore air in "+poi.name);
    }
    static IEnumerator Restore(World w,PrefabInstance poi,long key){
        var routine=poi.ResetBlocksAndRebuild(w,FastTags<TagGroup.Global>.Parse("clear,fetch"),key);
        while(routine.MoveNext())yield return routine.Current;
        Emit("[Dungeons] Restored "+poi.name);
    }
    static IEnumerator Stress(World w,string name,Vector3i sample,Dictionary<Vector3i,BlockValue> structure,bool ceiling){
        Emit("[Dungeons] Stress started "+name+" mode="+(ceiling?"ceiling":"floor")+" at "+sample+" structure="+structure.Count);
        w.SetBlocksRPC(new List<BlockChangeInfo>{new BlockChangeInfo(new BlockValueRef(sample),Block.GetBlockValue("woodShapes:cube",false))});
        yield return new WaitForSeconds(12);
        int changed=0;foreach(var cell in structure)if(w.GetBlock(cell.Key).rawData!=cell.Value.rawData)changed++;
        bool placed=w.GetBlock(sample).type==Block.GetBlockValue("woodShapes:cube",false).type;
        if(changed>0||(!ceiling&&!placed)){Emit("[Dungeons] FAIL stress "+name+" changed structural cells="+changed+" testBlockPresent="+placed);yield break;}
        if(placed)w.SetBlocksRPC(new List<BlockChangeInfo>{new BlockChangeInfo(new BlockValueRef(sample),BlockValue.Air)});
        yield return new WaitForSeconds(12);
        changed=0;foreach(var cell in structure)if(w.GetBlock(cell.Key).rawData!=cell.Value.rawData)changed++;
        Emit(changed==0?"[Dungeons] PASS stress "+name+" mode="+(ceiling?"ceiling":"floor")+" preserved "+structure.Count+" structural cells through placement/removal":"[Dungeons] FAIL stress removal "+name+" changed structural cells="+changed);
    }
    public static void RepairSmugglerTorch(Prefab p){
        string allowed=Path.GetFullPath(ModManager.GetMod("DelveWayrest",true).Path)+Path.DirectorySeparatorChar;
        if(p.PrefabName!="delve_dungeon_cave_11"||!Path.GetFullPath(p.location.FullPath).StartsWith(allowed,StringComparison.OrdinalIgnoreCase))throw new Exception("Torch repair destination is outside the isolated mod");
        var original=new Prefab();if(!original.Load(p.location,true,true,false,false))throw new Exception("Cannot copy original");
        // This decorative surface torch sits on two thin metal posts above a
        // weak cave span. Remove the unsupported assembly, leaving the cave,
        // encounters and other lighting intact; do not bypass native physics.
        var cells=new[]{new Vector3i(15,25,13),new Vector3i(15,26,13),new Vector3i(15,26,12)};
        foreach(var pos in cells){
            var b=p.GetBlock(pos.x,pos.y,pos.z);string expected=pos.z==12?"wallTorchLight":"corrugatedMetalShapes:pillar0.025Middle";
            if(!b.isair&&b.Block.GetBlockName()!=expected)throw new Exception("Unexpected torch repair cell "+pos+": "+b.Block.GetBlockName());
            if(p.triggerData.ContainsKey(pos)||p.IsWater(pos.x,pos.y,pos.z))throw new Exception("Gameplay metadata at repair cell");
            p.SetBlock(pos.x,pos.y,pos.z,BlockValue.Air);p.SetTexture(pos.x,pos.y,pos.z,new TextureFullArray(0));
        }
        string xml=File.ReadAllText(p.location.FullPathNoExtension+".xml");
        if(!p.Save(p.location,true))throw new Exception("Torch repair save failed");
        File.WriteAllText(p.location.FullPathNoExtension+".xml",xml);p.AddAllChildBlocks();
        var check=new Prefab();if(!check.Load(p.location,true,true,false,false))throw new Exception("Torch repair reload failed");
        var changed=new HashSet<Vector3i>(cells);
        for(int y=0;y<p.size.y;y++)for(int z=0;z<p.size.z;z++)for(int x=0;x<p.size.x;x++){
            var pos=new Vector3i(x,y,z);
            if(check.GetBlock(x,y,z).rawData!=p.GetBlock(x,y,z).rawData||check.GetTexture(x,y,z)!=p.GetTexture(x,y,z))throw new Exception("Torch serialization mismatch");
            if(!changed.Contains(pos)&&(check.GetBlock(x,y,z).rawData!=original.GetBlock(x,y,z).rawData||check.GetTexture(x,y,z)!=original.GetTexture(x,y,z)))throw new Exception("Changed outside torch assembly");
        }
        Emit("[Dungeons] PASS torch repair: three decorative cells removed; all other cells and quest metadata preserved; native serialization verified. Test in a fresh save.");
    }
    public static void Reinforce(Prefab p){
        string allowed=Path.GetFullPath(ModManager.GetMod("DelveWayrest",true).Path)+Path.DirectorySeparatorChar;
        if(p.PrefabName!="delve_dungeon_cave_12"||!Path.GetFullPath(p.location.FullPath).StartsWith(allowed,StringComparison.OrdinalIgnoreCase))throw new Exception("Reinforcement destination is outside the isolated mod");
        var original=new Prefab();if(!original.Load(p.location,true,true,false,false))throw new Exception("Cannot copy original");
        var changed=new HashSet<Vector3i>();var report=new XmlDocument();report.LoadXml("<supports/>");
        var pillar=Block.GetBlockValue("cobblestoneShapes:cube",false);if(pillar.isair)throw new Exception("Missing native masonry");
        long paint=0;for(int face=0;face<6;face++)paint|=63L<<(face*8);
        foreach(int targetZ in new[]{5,12,19})foreach(int targetX in new[]{5,12,19}){
            bool found=false;
            for(int radius=0;radius<=2&&!found;radius++)for(int dz=-radius;dz<=radius&&!found;dz++)for(int dx=-radius;dx<=radius&&!found;dx++){
                if(Math.Max(Math.Abs(dx),Math.Abs(dz))!=radius)continue;
                int x=targetX+dx,z=targetZ+dz;bool clear=true;
                string bottom=original.GetBlock(x,0,z).Block.GetBlockName(),top=original.GetBlock(x,24,z).Block.GetBlockName();
                if((!bottom.StartsWith("terr")&&bottom!="cobblestoneShapes:cube")||(!top.StartsWith("terr")&&top!="cobblestoneShapes:cube"))continue;
                for(int y=0;y<=24;y++){
                    var block=original.GetBlock(x,y,z);var pos=new Vector3i(x,y,z);
                    if((!block.isair&&!block.Block.GetBlockName().StartsWith("terr")&&block.Block.GetBlockName()!="cobblestoneShapes:cube")||original.IsWater(x,y,z)||original.triggerData.ContainsKey(pos)){clear=false;break;}
                }
                if(!clear)continue;
                for(int y=0;y<=24;y++){var pos=new Vector3i(x,y,z);p.SetBlock(x,y,z,pillar);p.SetTexture(x,y,z,new TextureFullArray(paint));changed.Add(pos);}
                var node=report.CreateElement("column");node.SetAttribute("x",x.ToString());node.SetAttribute("z",z.ToString());node.SetAttribute("y","0-24");report.DocumentElement.AppendChild(node);found=true;
            }
            if(!found)throw new Exception("No safe pillar near "+targetX+","+targetZ);
        }
        string xml=File.ReadAllText(p.location.FullPathNoExtension+".xml");
        if(!p.Save(p.location,true))throw new Exception("Reinforced save failed");
        File.WriteAllText(p.location.FullPathNoExtension+".xml",xml);p.AddAllChildBlocks();
        var check=new Prefab();if(!check.Load(p.location,true,true,false,false))throw new Exception("Reinforced reload failed");
        for(int y=0;y<p.size.y;y++)for(int z=0;z<p.size.z;z++)for(int x=0;x<p.size.x;x++){
            var pos=new Vector3i(x,y,z);
            if(check.GetBlock(x,y,z).rawData!=p.GetBlock(x,y,z).rawData||check.GetTexture(x,y,z)!=p.GetTexture(x,y,z))throw new Exception("Support serialization mismatch");
            if(!changed.Contains(pos)&&(check.GetBlock(x,y,z).rawData!=original.GetBlock(x,y,z).rawData||check.GetTexture(x,y,z)!=original.GetTexture(x,y,z)))throw new Exception("Changed outside support columns");
        }
        report.DocumentElement.SetAttribute("changedCells",changed.Count.ToString());
        report.Save(Path.Combine(ModManager.GetMod("AlliumTools",true).Path,"old-warden-supports.xml"));
        Emit("[Dungeons] Reinforced isolated prefab with "+changed.Count+" native masonry cells; all other cells and quest metadata preserved. Restart in a fresh test save before testing.");
    }

}
