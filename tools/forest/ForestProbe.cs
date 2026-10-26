using System;
using System.Collections.Generic;
using System.IO;
using System.Xml;
using System.Reflection;
using UnityEngine;
using DelveForest;

public class ConsoleCmdForestProbe:ConsoleCmdAbstract
{
    static ChunkManager.ChunkObserver observer;
    public override string[] getCommands(){return new[]{"forestprobe"};}
    public override string getDescription(){return "Developer fixture: load [x z] | verify | poi x z | spawn x z | spawned";}
    static void Check(bool c,string text){if(!c)throw new Exception(text);}
    static FieldInfo Field(string name){return typeof(SleeperVolume).GetField(name,BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic);}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        var w=GameManager.Instance.World;
        if(w==null || w.IsRemote() || Delve.Core.Progress==null){SdtdConsole.Instance.Output("[Forest] Wait for StartGame done.");return;}
        try {
            if(args.Count==0)throw new Exception(getDescription());
            if(args[0]=="load") {
                int x=args.Count>2?int.Parse(args[1]):-2225,z=args.Count>2?int.Parse(args[2]):-1940;
                if(observer!=null)GameManager.Instance.RemoveChunkObserver(observer);
                observer=GameManager.Instance.AddChunkObserver(new Vector3(x,80,z),false,4,3);
                SdtdConsole.Instance.Output("[Forest] Loading fixture terrain "+x+","+z);return;
            }
            if(args[0]=="verify") {
                var xml=new XmlDocument();xml.Load(Path.Combine(ModManager.GetMod("ZDelveForest",true).Path,"Bestiary.xml"));
                int count=0;
                foreach(XmlElement def in xml.SelectNodes("/bestiary/creature")) {
                    string name=def.GetAttribute("id");var e=EntityFactory.CreateEntity(EntityClass.FromString(name),new Vector3(-2225,80,-1940)) as EntityAlive;
                    Check(e!=null,"Missing "+name);
                    try {
                        int hp=int.Parse(def.GetAttribute("hp"));bool animal=def.GetAttribute("parent").StartsWith("animal");
                        Check(animal?e.GetMaxHealth()>=Math.Floor(hp*.8)&&e.GetMaxHealth()<=Math.Ceiling(hp*1.15):e.GetMaxHealth()==hp,name+" HP "+e.GetMaxHealth());
                        var hand=ItemClass.GetItem(name+"Attack",false);
                        Check(hand!=null && hand.type!=0,"Missing attack "+name);
                        float damage=EffectManager.GetValue(PassiveEffects.EntityDamage,hand,0,e);
                        Check(Math.Abs(damage-float.Parse(def.GetAttribute("damage")))<.01f,name+" damage "+damage);
                        float armor=EffectManager.GetValue(PassiveEffects.PhysicalDamageResist,null,0,e);
                        Check(Math.Abs(armor-float.Parse(def.GetAttribute("armor")))<.01f,name+" armor "+armor);
                        Check(def.GetAttribute("parent").StartsWith("animal")?e.EntityClass.Properties.GetString("DelveTint")==def.GetAttribute("color"):e.EntityClass.Properties.GetString("MatColor")==name+"Color",name+" material identity");
                        if(name=="delveCrystalStag" || name=="delveThornbackBoar" || name=="delveGloomcat") {
                            int before=Delve.Core.Progress.CorruptedKills;
                            var data=new ModEvents.SEntityKilledData(e,null);Delve.Core.Killed(ref data);
                            Check(Delve.Core.Progress.CorruptedKills==before,"Wildlife must not credit corruption kills");
                        }
                        if(name=="delveCrystalStag") Check(!e.EntityClass.bIsEnemyEntity,"Crystal Stag must remain neutral");
                        count++;
                    } finally {UnityEngine.Object.Destroy(e.gameObject);}
                }
                foreach(string name in new[]{"delveForest_ZombiesAll","delveForest_ZombiesNight","delveForest_WildGameForestNight","delveForest_EnemyAnimalsForest","delveArborNight"})Check(EntityGroups.list[name]!=null,"Missing biome pool "+name);
                SdtdConsole.Instance.Output("[Forest] PASS: "+count+" native entities, HP, attack damage, armor, material keys, neutral stag, wildlife campaign exclusions and biome pools. Rendering/combat not asserted.");return;
            }
            if(args[0]=="heavy") {
                foreach(var connected in w.GetPlayers())throw new Exception("Fixture requires no connected players");
                var position=new Vector3(-2225,w.GetHeightAt(-2225,-1940)+1,-1940);
                var target=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),position+new Vector3(2,0,0)) as EntityPlayer;
                target.world=w;
                try {
                    foreach(string name in new[]{"delveWarpedBrute","delveThornbackBoar"}) {
                        var enemy=EntityFactory.CreateEntity(EntityClass.FromString(name),position) as EntityAlive;
                        w.SpawnEntityInWorld(enemy);
                        try {
                            var cycle=enemy.GetComponent<HeavyAttackCycle>();Check(cycle!=null,"Heavy behavior not attached: "+name);
                            enemy.SetAttackTarget(target,120);float normalSpeed=enemy.GetMoveSpeedAggro();
                            var attack=ItemClass.GetItem(name+"Attack",false);float baseDamage=EffectManager.GetValue(PassiveEffects.EntityDamage,attack,0,enemy);
                            string[] buffs={"delveForestBrace","delveForestRush","delveForestSpent"};
                            for(int phase=0;phase<3;phase++) {
                                typeof(HeavyAttackCycle).GetField("next",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(cycle,0f);
                                typeof(HeavyAttackCycle).GetMethod("Update",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(cycle,null);
                                enemy.Buffs.Tick();Check(enemy.Buffs.HasBuff(buffs[phase]),name+" missing phase "+phase);
                                Check(phase==1?enemy.GetMoveSpeedAggro()>normalSpeed:enemy.GetMoveSpeedAggro()<normalSpeed,name+" phase movement "+phase);
                                float damage=EffectManager.GetValue(PassiveEffects.EntityDamage,attack,0,enemy);
                                Check(Math.Abs(damage-baseDamage*(phase==1?1.25f:.5f))<.01f,name+" phase attack damage "+phase);
                            }
                        } finally {w.RemoveEntity(enemy.entityId,EnumRemoveEntityReason.Despawned);}
                    }
                }finally{UnityEngine.Object.Destroy(target.gameObject);}
                SdtdConsole.Instance.Output("[Forest] PASS native Brute/Thornback component attachment and brace/rush/recovery movement and attack damage states.");return;
            }
            if(args[0]=="spawned") {
                int n=0;foreach(var e in w.EntityAlives)if(e!=null && EntityClass.GetEntityClassName(e.entityClass)=="delveImp") {n++;SdtdConsole.Instance.Output("[Forest] live Imp "+e.entityId+" at "+e.position);}
                Check(n>0,"No native sleeper Imp found");SdtdConsole.Instance.Output("[Forest] PASS actual asynchronous sleeper spawned the substituted Imp.");return;
            }
            int px=int.Parse(args[1]),pz=int.Parse(args[2]);
            var poi=w.GetPOIAtPosition(new Vector3(px,w.GetHeightAt(px,pz),pz),null,null);
            Check(poi!=null && poi.prefab!=null,"No loaded POI");PoiRule rule;
            Check(ModApi.Pois.TryGetValue(poi.prefab.PrefabName,out rule),"Unassigned POI "+poi.prefab.PrefabName);
            Check(poi.sleeperVolumes!=null && poi.sleeperVolumes.Count>rule.Volume,"Sleeper volumes not loaded");
            var volume=poi.sleeperVolumes[rule.Volume];int normal=EntityClass.FromString("zombieBoe");
            Check(ModApi.Replacement(volume,1,0,normal)=="delveCorruptedWalker","Starter replacement");
            Check(ModApi.Replacement(volume,81,0,normal)==ForestRules.Replacement(rule.Kind,81,0),"Advanced replacement");
            Check(ModApi.Replacement(volume,81,2,normal)==null,"No excess specialist");
            Check(ModApi.Replacement(volume,81,0,EntityClass.FromString("delveImp"))==null,"Respawn identity retained");
            if(args[0]=="spawn") {
                foreach(var p in w.GetPlayers())throw new Exception("Do not run synthetic spawn fixture with connected players");
                Check(rule.Kind=="imp","Use the imp test cabin");
                Check(volume.GetSpawnPoints().Count>0,"No native sleeper positions");
                Field("gameStage").SetValue(volume,81);Field("numSpawned").SetValue(volume,0);
                var point=volume.GetSpawnPoints()[0];
                BlockSleeper marker=point.GetBlock();
                Check(marker!=null,"Native sleeper marker missing at "+point.pos);
                Check(!marker.ExcludesWalkType(EntityAlive.GetSpawnWalkType(EntityClass.GetEntityClass(EntityClass.FromString("delveImp")))) ,"Selected marker excludes Imp pose");
                Check(volume.Spawn(w,normal,0,marker),"Native asynchronous spawn refused");
                SdtdConsole.Instance.Output("[Forest] Queued actual native sleeper spawn; run spawned after engine update.");return;
            }
            SdtdConsole.Instance.Output("[Forest] PASS loaded "+poi.prefab.PrefabName+" selected volume "+rule.Volume+"/"+poi.sleeperVolumes.Count+" kind "+rule.Kind+"; progression, density and respawn guards.");
        }catch(Exception ex){SdtdConsole.Instance.Output("[Forest] FAIL "+ex);}
    }
}
