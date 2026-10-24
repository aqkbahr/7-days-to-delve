using System;
using System.Collections.Generic;
using UnityEngine;

public class ConsoleCmdWayrestJobs : ConsoleCmdAbstract
{
    public override string[] getCommands() { return new[] { "wayrestjobs" }; }
    public override string getDescription() { return "Development-only native Wayrest job selection checks."; }
    public override void Execute(List<string> args, CommandSenderInfo sender)
    {
        EntityPlayer player = null;
        try
        {
            World w = GameManager.Instance.World;
            EntityTrader steward = null;
            foreach(var entity in w.EntityAlives)
                if(EntityClass.GetEntityClassName(entity.entityClass)=="delveWayrestSteward") steward=entity as EntityTrader;
            if(steward==null) throw new Exception("Load Wayrest chunks first.");
            // An empty dedicated server pauses entity updates. Perform the
            // native initialization tick a nearby human normally triggers.
            steward.OnUpdateLive();
            if(steward.traderArea==null) throw new Exception("Steward is not bound to its native trader area");
            foreach(string id in new[]{"delveWayrestFetch","delveWayrestClear","delveWayrestFetchClear","delveWayrestReclamation","delveWayrestOnward"})
                if(QuestClass.CreateQuest(id)==null) throw new Exception("Missing quest "+id);
            if(!(QuestClass.CreateQuest("delveWayrestReclamation").Objectives[0] is ObjectiveDelveWayrest)) throw new Exception("Wrong journal objective type");
            player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),steward.position) as EntityPlayer;
            player.world=w;
            SdtdConsole.Instance.Output("[Wayrest] native POI jobs="+QuestJournal.POIQuestsEnabled+" zombies="+GameStats.GetBool(EnumGameStats.IsSpawnEnemies));
            var eligible=QuestEventManager.Current.GetPrefabsByDifficultyTier(1);
            SdtdConsole.Instance.Output("[Wayrest] registered tier1="+(eligible==null?0:eligible.Count));
            Quest sample=QuestClass.CreateQuest("delveWayrestFetch");sample.SetupTags();
            if(eligible!=null) foreach(var poi in eligible)
                if(w.GetBiomeInWorld(poi.boundingBoxPosition.x,poi.boundingBoxPosition.z).m_sBiomeName=="pine_forest")
                    SdtdConsole.Instance.Output("[Wayrest] candidate "+poi.name+" sleepers="+poi.prefab.SleeperVolumeList.AnyUsedEntry+" tagMatch="+poi.prefab.GetQuestTag(sample.QuestTags));
            var kinds=new HashSet<string>();var sites=new HashSet<string>();int offers=0;
            for(int attempt=0;attempt<40;attempt++)
            {
                var list=steward.PopulateActiveQuests(player,6,0);
                if(list==null || list.Count==0) throw new Exception("Empty native board");
                foreach(Quest q in list)
                {
                    if(q.ID=="delvewayrestonward") throw new Exception("Onward offered before ten jobs");
                    if(!Delve.WayrestCampaign.IsJob(q.ID)) throw new Exception("Wrong quest pool "+q.ID);
                    if(q.QuestClass.DifficultyTier!=1) throw new Exception("Tier leak");
                    Vector3 pos=q.GetLocation();
                    if(w.GetBiomeInWorld((int)pos.x,(int)pos.z).m_sBiomeName!="pine_forest") throw new Exception("Biome leak "+pos);
                    kinds.Add(q.ID);sites.Add(pos.ToString());offers++;
                }
            }
            if(kinds.Count!=3 || sites.Count<8) throw new Exception("Insufficient variety "+kinds.Count+" types / "+sites.Count+" sites");
            player.Buffs.SetCustomVar("delveWayrestReady",1,false);
            bool onward=false;
            foreach(Quest q in steward.PopulateActiveQuests(player,1,0))
                if(q.ID=="delvewayrestonward")
                {
                    onward=true;
                    SdtdConsole.Instance.Output("[Wayrest] Onward destination="+q.GetLocation());
                    if(w.GetBiomeInWorld((int)q.GetLocation().x,(int)q.GetLocation().z).m_sBiomeName!="burnt_forest") throw new Exception("Onward not Arbor");
                }
            if(!onward) throw new Exception("Onward not available at ten jobs");
            SdtdConsole.Instance.Output("[Wayrest] PASS native board: "+offers+" offers / "+kinds.Count+" quest types / "+sites.Count+" Forest sites; Tier 1 cap; onward locked then unlocked.");
        }
        catch(Exception ex) { SdtdConsole.Instance.Output("[Wayrest] FAIL "+ex); }
        finally { if(player!=null) UnityEngine.Object.Destroy(player.gameObject); }
    }
}

public class ConsoleCmdWayrestState : ConsoleCmdAbstract
{
    public override string[] getCommands() { return new[] { "wayreststate" }; }
    public override string getDescription() { return "Development-only shared tally and next-morning delta fixture; restores original state."; }
    public override void Execute(List<string> args, CommandSenderInfo sender)
    {
        World w=GameManager.Instance.World;var original=Delve.Core.Progress;ulong time=w.worldTime;
        EntityPlayer a=null,b=null;var blocks=new List<BlockChangeInfo>();
        try
        {
            foreach(int x in new[]{25,34}) for(int y=2;y<=6;y++)
            {
                var pos=new Vector3i(-2711+x,63+y,-2178);
                if(w.GetChunkSync(pos.x>>4,pos.z>>4)==null) throw new Exception("Load Wayrest first");
                blocks.Add(new BlockChangeInfo(new BlockValueRef(pos),w.GetBlock(pos.x,pos.y,pos.z)));
            }
            Delve.Core.Progress=new Delve.WorldProgress();
            a=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),new Vector3(-2680,65,-2132)) as EntityPlayer;
            b=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),new Vector3(-2680,65,-2132)) as EntityPlayer;
            a.world=w;b.world=w;w.Players.Add(a.entityId,a);w.Players.Add(b.entityId,b);
            a.Buffs.SetCustomVar(Delve.WayrestCampaign.ReceiptPrefix+"fixture-a",1,false);
            b.Buffs.SetCustomVar(Delve.WayrestCampaign.ReceiptPrefix+"fixture-a",1,false);
            Delve.WayrestCampaign.Tick(w);
            if(Delve.Core.Progress.WayrestReceipts.Count!=1 || b.Buffs.GetCustomVar("delveWayrestJobs")!=1) throw new Exception("Shared duplicate/sync failed");
            for(int i=1;i<10;i++) a.Buffs.SetCustomVar(Delve.WayrestCampaign.ReceiptPrefix+"fixture-"+i,1,false);
            Delve.WayrestCampaign.Tick(w);
            if(Delve.Core.Progress.WayrestReceipts.Count!=10 || b.Buffs.GetCustomVar("delveWayrestReady")!=1 || Delve.Core.Progress.WayrestRefurbished) throw new Exception("Milestone/same-day gate failed");
            b.Buffs.SetCustomVar("%delveArborArrival",1,false);Delve.WayrestCampaign.Tick(w);
            if(!Delve.Core.Progress.ArborReached || a.Buffs.GetCustomVar("delveArborUnlocked")!=1) throw new Exception("Shared onward failed");
            w.worldTime=(ulong)(Delve.Core.Progress.WayrestCompletedDay*24000+4100);
            Delve.WayrestCampaign.TryRefurbish(w);
            if(!Delve.Core.Progress.WayrestRefurbished) throw new Exception("Next opening refurbishment failed");
            if(w.GetBlock(-2686,65,-2178).type!=Block.GetBlockValue("cobblestoneShapes:cube",false).type) throw new Exception("Refurbishment did not change block");
            SdtdConsole.Instance.Output("[Wayrest] PASS shared receipt dedup, 10-job cap/unlock, second-player sync, onward state, same-day deferral and next-opening native block delta.");
        }
        catch(Exception ex) { SdtdConsole.Instance.Output("[Wayrest] FAIL state "+ex); }
        finally
        {
            w.worldTime=time;
            if(a!=null){w.Players.Remove(a.entityId);UnityEngine.Object.Destroy(a.gameObject);}
            if(b!=null){w.Players.Remove(b.entityId);UnityEngine.Object.Destroy(b.gameObject);}
            if(blocks.Count>0) w.SetBlocksRPC(blocks);
            Delve.Core.Progress=original;Delve.Core.Save();
        }
    }
}
