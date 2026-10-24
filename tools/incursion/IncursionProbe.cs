using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;
using Delve;

// Developer-only mod. Never distributed with player packages.
public class ConsoleCmdIncursionProbe : ConsoleCmdAbstract
{
    static ChunkManager.ChunkObserver observer;
    static FieldInfo Field(string name) { return typeof(Core).GetField(name,BindingFlags.NonPublic|BindingFlags.Static); }
    static void Check(bool condition,string message) { if(!condition) throw new Exception(message); }
    static void Tick() { Field("nextTick").SetValue(null,0f); var data=new ModEvents.SGameUpdateData();Core.Update(ref data); var boss=Boss(GameManager.Instance.World);if(boss!=null)boss.Buffs.Tick(); }
    static EntityAlive Boss(World w) { return w.GetEntity((int)Field("activeBoss").GetValue(null)) as EntityAlive; }
    public override string[] getCommands() { return new[]{"incursionprobe"}; }
    public override string getDescription() { return "Isolated dev harness: load | verify"; }
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        World w=GameManager.Instance.World;
        if(w==null || !Core.IsServer || Core.Progress==null) { SdtdConsole.Instance.Output("[Incursion] Wait for an isolated server world to finish loading.");return; }
        foreach(var existing in w.GetPlayers()) { SdtdConsole.Instance.Output("[Incursion] Refusing fixture tests while a player is connected.");return; }
        if((int)Field("activeBoss").GetValue(null)>=0) { SdtdConsole.Instance.Output("[Incursion] Refusing to interrupt an existing encounter.");return; }
        if(args.Count>0 && args[0]=="load") {
            if(observer!=null) GameManager.Instance.RemoveChunkObserver(observer);
            observer=GameManager.Instance.AddChunkObserver(new Vector3(0,80,0),false,5,3);
            SdtdConsole.Instance.Output("[Incursion] Requested fixture chunks around 0,0.");return;
        }
        var original=Core.Progress;
        EntityPlayer a=null,b=null;
        var spawned=new List<int>();
        try {
            Check(w.GetChunkSync(0,0)!=null,"Load fixture chunks first");
            Check((int)Field("activeBoss").GetValue(null)<0,"A real encounter is already active");
            Core.Progress=new WorldProgress();
            Vector3 position=new Vector3(0,w.GetHeightAt(0,0)+1,0);
            a=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),position) as EntityPlayer;
            b=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),position+new Vector3(2,0,0)) as EntityPlayer;
            a.world=w;b.world=w;
            // Synchronous fixture participants, never normal world player updates.
            w.Players.Add(a.entityId,a);w.Entities.Add(a.entityId,a);
            w.Players.Add(b.entityId,b);w.Entities.Add(b.entityId,b);
            string result=Core.SpawnBoss(a,true);
            EntityAlive boss=Boss(w);Check(boss!=null,result);spawned.Add(boss.entityId);
            Check(boss.GetMaxHealth()==1350 && boss.Health==1350,"Two-player health scaling");
            float normal=boss.GetMoveSpeedAggro();
            Field("encounterStarted").SetValue(null,Time.realtimeSinceStartup-13);Tick();
            Check(boss.Buffs.HasBuff("delveWardenWindup") && boss.GetMoveSpeedAggro()<normal,"Warned slowdown");
            Field("encounterStarted").SetValue(null,Time.realtimeSinceStartup-17);Tick();
            Check(boss.Buffs.HasBuff("delveWardenAssault") && !boss.Buffs.HasBuff("delveWardenWindup") && boss.GetMoveSpeedAggro()>normal,"Assault speed and transition");
            Field("encounterStarted").SetValue(null,Time.realtimeSinceStartup-23);Tick();
            Check(boss.Buffs.HasBuff("delveWardenRecovery") && boss.GetMoveSpeedAggro()<normal,"Recovery window");
            w.Entities.Remove(a.entityId);w.Players.Remove(a.entityId);Tick();
            Check(Boss(w)!=null,"One disconnect must not wipe remaining participant");
            w.Entities.Remove(b.entityId);w.Players.Remove(b.entityId);Tick();
            Check(Boss(w)==null && !Core.Progress.WardenDefeated,"Full disconnect withdraws without victory");
            w.Entities.Add(a.entityId,a);w.Players.Add(a.entityId,a);
            result=Core.SpawnBoss(a,true);boss=Boss(w);Check(boss!=null,result);spawned.Add(boss.entityId);
            Check(boss.GetMaxHealth()==900,"Solo retry health");
            Field("encounterStarted").SetValue(null,Time.realtimeSinceStartup-601);Tick();
            Check(Boss(w)==null && !Core.Progress.WardenDefeated,"Test timeout withdraws");
            Check(w.IsDaytime(),"Run the fixture during daytime to check dawn withdrawal");
            result=Core.SpawnBoss(a,true);boss=Boss(w);Check(boss!=null,result);spawned.Add(boss.entityId);
            Field("manualEncounter").SetValue(null,false);Tick();
            Check(Boss(w)==null && !Core.Progress.WardenDefeated,"Natural encounter withdraws in daylight");
            result=Core.SpawnBoss(a,true);boss=Boss(w);Check(boss!=null,result);spawned.Add(boss.entityId);
            boss.SetDead();Tick();
            Check(Core.Progress.WardenDefeated,"Dead boss credits victory");
            a.SetDead();Tick();Check(Core.Progress.WardenDefeated,"Later wipe preserves victory");
            Check(Core.SpawnBoss(a,true).Contains("already defeated"),"Victory prevents duplicate encounter");
            foreach(string name in new[]{"delveCorruptedWalker","delvePossessedSoldier","delveImp","delveHellhound","delveDemonSpawn","delveWarpedBrute"}) {
                EntityAlive enemy=EntityFactory.CreateEntity(EntityClass.FromString(name),position+new Vector3(30,0,30)) as EntityAlive;
                Check(enemy!=null && enemy.GetMaxHealth()>0,"Reusable enemy instantiation: "+name);
                UnityEngine.Object.Destroy(enemy.gameObject);
            }
            SdtdConsole.Instance.Output("[Incursion] PASS: native spawn; solo/co-op health; movement buffs and phase transitions; partial/full disconnect; timeout; dawn; retry; death credit; victory survives wipe; duplicate prevention; six reusable enemy instances. Synthetic fixtures, not human combat.");
        } catch(Exception ex) { SdtdConsole.Instance.Output("[Incursion] FAIL "+ex); }
        finally {
            foreach(int id in spawned) if(w.GetEntity(id)!=null) w.RemoveEntity(id,EnumRemoveEntityReason.Despawned);
            if(a!=null){w.Entities.Remove(a.entityId);w.Players.Remove(a.entityId);UnityEngine.Object.Destroy(a.gameObject);}
            if(b!=null){w.Entities.Remove(b.entityId);w.Players.Remove(b.entityId);UnityEngine.Object.Destroy(b.gameObject);}
            Field("activeBoss").SetValue(null,-1);
            Core.Progress=original;Core.Save();
        }
    }
}
