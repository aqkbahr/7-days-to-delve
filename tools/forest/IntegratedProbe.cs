using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;
using DelveForest;

public class ConsoleCmdForestIntegrated:ConsoleCmdAbstract
{
    static void Check(bool ok,string why){if(!ok)throw new Exception(why);}
    static FieldInfo Field(Type t,string n){return t.GetField(n,BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.Static);}
    public override string[] getCommands(){return new[]{"forestintegrated"};}
    public override string getDescription(){return "Isolated integration checks: verify | poi x z | horde | restart | timeline | damage";}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        var w=GameManager.Instance.World;
        if(w==null || w.IsRemote() || Delve.Core.Progress==null){SdtdConsole.Instance.Output("Wait for StartGame done");return;}
        foreach(var p in w.GetPlayers()){SdtdConsole.Instance.Output("Requires no connected players");return;}
        EntityPlayer player=null;var spawned=new List<int>();
        try {
            string command=args.Count==0?"verify":args[0];
            if(command=="verify") {
                player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),new Vector3(0,80,0)) as EntityPlayer;player.world=w;
                Check(ModApi.Pois.Count==18,"Garden aliases");
                string[] materials={"delveThornhide","delveGloomPelt","delveForestCrystal"};
                string[] outputs={"resourceLeather","resourceLeather","delveEmberSalts"};int[] counts={3,5,3};
                for(int i=0;i<3;i++) {
                    bool found=false;
                    foreach(var recipe in CraftingManager.GetRecipes(outputs[i]))
                        if(recipe.ingredients.Count==1 && recipe.ingredients[0].itemValue.ItemClass.GetItemName()==materials[i]) {
                            Check(recipe.count==counts[i] && recipe.ingredients[0].count==1,"Conversion quantities "+materials[i]);
                            Check(recipe.CanCraft(new List<ItemStack>{new ItemStack(ItemClass.GetItem(materials[i],false),1)},player,-1),"Conversion craftable "+materials[i]);
                            Check(!recipe.CanCraft(new List<ItemStack>(),player,-1),"Missing ingredient rejected "+materials[i]);found=true;
                        }
                    Check(found,"Loaded conversion "+materials[i]);
                }
                foreach(int level in new[]{1,5,10,15,20,21}) {
                    ForestHordeContext.Inside=true;ForestHordeContext.First=false;ForestHordeContext.Level=level;
                    int last=-1;
                    for(int n=0;n<40;n++) {
                        int id=EntityGroups.GetRandomEntityFromGroupMaxTier("feralHordeStageGS103",EntityFactory.MaxEntityTier,ref last,true,false,null);
                        Check(id!=-1 && EntityClass.GetEntityClass(id)!=null,"Horde native tier selection "+level);
                    }
                }
                SdtdConsole.Instance.Output("[Integrated] PASS 18 POI policies; three loaded/craftable resource conversions; native tier-limited horde selections at levels 1,5,10,15,20,21.");return;
            }
            if(command=="poi") {
                int x=int.Parse(args[1]),z=int.Parse(args[2]);
                var poi=w.GetPOIAtPosition(new Vector3(x,w.GetHeightAt(x,z),z),null,null);PoiRule rule;
                Check(poi!=null && ModApi.Pois.TryGetValue(poi.prefab.PrefabName,out rule),"POI assignment");
                rule=ModApi.Pois[poi.prefab.PrefabName];var volume=poi.sleeperVolumes[rule.Volume];
                player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),new Vector3(x,w.GetHeightAt(x,z)+1,z)) as EntityPlayer;
                player.world=w;w.Players.Add(player.entityId,player);w.Entities.Add(player.entityId,player);
                int checkedMarkers=0;
                foreach(int level in new[]{1,5,6,10,11,15,16,20}) {
                    player.Progression.Level=level;
                    string expected=ForestRules.ReplacementAtLevel(rule.Kind,level,0);
                    Check(ModApi.Replacement(volume,500,0,EntityClass.FromString("zombieBoe"))==expected,"Character-level policy "+level);
                    foreach(var point in volume.GetSpawnPoints()) {
                        var marker=point.GetBlock();if(marker==null)continue;
                        int original=EntityClass.FromString("zombieBoe"),id=original;
                        ForestSleepers.Prefix(volume,w,ref id,marker,0,500);
                        bool supported=!marker.ExcludesWalkType(EntityAlive.GetSpawnWalkType(EntityClass.GetEntityClass(EntityClass.FromString(expected))));
                        Check(id==(supported?EntityClass.FromString(expected):original),"Marker exclusion guard");checkedMarkers++;
                    }
                }
                Check(checkedMarkers>0,"Loaded native markers");
                volume.DespawnAndReset(w);
                Check(!(bool)Field(typeof(SleeperVolume),"isSpawned").GetValue(volume),"Native reset");
                Check(ModApi.Replacement(volume,500,0,EntityClass.FromString("delveImp"))==null,"Custom respawn identity");
                SdtdConsole.Instance.Output("[Integrated] PASS POI "+poi.prefab.PrefabName+" eight level boundaries, "+checkedMarkers+" marker checks, native reset and respawn identity.");return;
            }
            if(command=="horde") {
                Check(w.GetChunkSync(0,0)!=null,"Load incursion fixture first");
                player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),new Vector3(0,w.GetHeightAt(0,0)+1,0)) as EntityPlayer;
                player.world=w;player.Progression.Level=20;w.Players.Add(player.entityId,player);w.Entities.Add(player.entityId,player);
                Field(typeof(EntityAlive),"bSpawned").SetValue(player,true);player.IsBloodMoonDead=false;
                var party=new AIDirectorBloodMoonParty(player,w.GetAIDirector().BloodMoonComponent,0);
                Check((bool)typeof(AIDirectorBloodMoonParty).GetMethod("IsPlayerATarget",BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic).Invoke(party,new object[]{player}),"Fixture is an eligible native horde target");
                typeof(AIDirectorBloodMoonParty).GetMethod("InitParty",BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic).Invoke(party,null);
                ((AIDirectorGameStagePartySpawner)Field(typeof(AIDirectorBloodMoonParty),"partySpawner").GetValue(party)).SetPartyLevel(103);
                var spawn=typeof(AIDirectorBloodMoonParty).GetMethod("SpawnZombie",BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic);
                int successes=0;
                for(int i=0;i<20 && successes<6;i++) {
                    var before=new HashSet<int>();foreach(var e in w.EntityAlives)before.Add(e.entityId);
                    bool ok=(bool)spawn.Invoke(party,new object[]{w,player,player.position,new Vector3(40,0,40)});
                    if(ok)successes++;
                    foreach(var e in new List<EntityAlive>(w.EntityAlives))if(!before.Contains(e.entityId)){spawned.Add(e.entityId);Check(!e.IsDead() && e.Health>0,"Horde enemy alive: "+e.EntityName);}
                    Check(!ForestHordeContext.Inside,"Horde context restored");
                }
                Check(successes>0,"Native horde spawn failed");
                SdtdConsole.Instance.Output("[Integrated] PASS native BloodMoon party spawned "+successes+" living enemies at level 20 / game stage 103; context restored; first-night persistence="+ForestCampaign.FirstNight+".");return;
            }
            if(command=="restart") {
                var data=new ModEvents.SGameStartDoneData();int night=ForestCampaign.FirstNight;
                ForestCampaign.Start(ref data);Check(ForestCampaign.FirstNight==night && night>0,"Persisted first night");
                SdtdConsole.Instance.Output("[Integrated] PASS first-night state reload "+night+".");return;
            }
            if(command=="damage") {
                int oldKills=Delve.Core.Progress.CorruptedKills;
                try {
                    foreach(string name in ModApi.Roster) {
                        var enemy=EntityFactory.CreateEntity(EntityClass.FromString(name),new Vector3(0,w.GetHeightAt(0,0)+1,0)) as EntityAlive;
                        w.SpawnEntityInWorld(enemy);spawned.Add(enemy.entityId);
                        SdtdConsole.Instance.Output("[Integrated] damage fixture "+name+" health="+enemy.Health+" max="+enemy.GetMaxHealth()+" dead="+enemy.IsDead());
                        int before=enemy.Health;
                        enemy.DamageEntity(new DamageSource(EnumDamageSource.External,EnumDamageTypes.Bashing),10,false,1f);
                        Check(enemy.Health<before && !enemy.IsDead(),"Receives damage "+name);
                        enemy.DamageEntity(new DamageSource(EnumDamageSource.Internal,EnumDamageTypes.Suicide),100000,false,1f);
                        Check(enemy.IsDead(),"Native death "+name);
                        if(name=="delveThornbackBoar" || name=="delveGloomcat" || name=="delveCrystalStag") {
                            string drop=name=="delveThornbackBoar"?"delveThornhide":name=="delveGloomcat"?"delveGloomPelt":"delveForestCrystal";
                            bool found=false;foreach(var item in enemy.EntityClass.itemsToDrop[EnumDropEvent.Harvest])if(item.name==drop && item.minCount>0)found=true;
                            Check(found,"Native corpse harvest table "+name);
                        }
                    }
                    SdtdConsole.Instance.Output("[Integrated] PASS nine reusable creatures receive native damage and die; three corpse harvest tables resolve. Player tool harvesting not simulated.");
                }finally{Delve.Core.Progress.CorruptedKills=oldKills;Delve.Core.Save();}
                return;
            }
            if(command=="timeline") {
                var original=Delve.Core.Progress;ulong time=w.GetWorldTime();int moon=GameStats.GetInt(EnumGameStats.BloodMoonDay);
                int skyMoon=(int)Field(typeof(SkyManager),"bloodmoonDay").GetValue(null);
                var active=Field(typeof(Delve.Core),"activeBoss");var tick=Field(typeof(Delve.Core),"nextTick");
                Check((int)active.GetValue(null)<0,"Existing boss");
                player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),new Vector3(0,w.GetHeightAt(0,0)+1,0)) as EntityPlayer;
                player.world=w;w.Players.Add(player.entityId,player);w.Entities.Add(player.entityId,player);
                int dawn=GameUtils.CalcDuskDawnHours(GameStats.GetInt(EnumGameStats.DayLightLength)).Item2;
                var trader=new TraderInfo();trader.UseOpenHours=false;
                var update=new ModEvents.SGameUpdateData();
                try {
                    Delve.Core.Progress=new Delve.WorldProgress();GameStats.Set(EnumGameStats.BloodMoonDay,7);
                    Field(typeof(SkyManager),"bloodmoonDay").SetValue(null,7);
                    ulong arrival=GameUtils.DayTimeToWorldTime(8,dawn-2,0);
                    w.SetTime(arrival);SkyManager.SetGameTime(arrival);
                    Check(!w.IsDaytime() && SkyManager.IsBloodMoonVisible(),"Native Blood Moon clock");
                    Check(!trader.IsOpen,"Settlement closed");
                    tick.SetValue(null,0f);Delve.Core.Update(ref update);
                    int first=(int)active.GetValue(null);Check(first>=0,"Automatic Warden arrival");spawned.Add(first);
                    Field(typeof(ForestCampaign),"next").SetValue(null,0f);ForestCampaign.Update(ref update);
                    var start=new ModEvents.SGameStartDoneData();Delve.Core.Start(ref start);ForestCampaign.Start(ref start);
                    Check(Delve.Core.Progress.LastAttemptDay==-1,"Interrupted encounter retry restored");
                    tick.SetValue(null,0f);Delve.Core.Update(ref update);
                    int retry=(int)active.GetValue(null);Check(retry>=0 && retry!=first,"Automatic retry after reload");spawned.Add(retry);
                    Check(w.GetEntity(first)==null,"Orphan removed");
                    ulong morning=GameUtils.DayTimeToWorldTime(8,dawn+1,0);w.SetTime(morning);SkyManager.SetGameTime(morning);
                    tick.SetValue(null,0f);Delve.Core.Update(ref update);
                    Check((int)active.GetValue(null)<0 && !Delve.Core.Progress.WardenDefeated,"Dawn withdrawal without victory");
                    Check(trader.IsOpen,"Settlement reopens");
                    SdtdConsole.Instance.Output("[Integrated] PASS native Blood Moon clock, automatic Warden arrival, interrupted encounter reload/retry, orphan cleanup, dawn withdrawal and settlement open-state restoration. Time advanced by fixture; not a full played night.");
                }finally {
                    foreach(int id in spawned)if(w.GetEntity(id)!=null)w.RemoveEntity(id,EnumRemoveEntityReason.Despawned);
                    active.SetValue(null,-1);Delve.Core.Progress=original;Delve.Core.Save();
                    w.SetTime(time);SkyManager.SetGameTime(time);GameStats.Set(EnumGameStats.BloodMoonDay,moon);Field(typeof(SkyManager),"bloodmoonDay").SetValue(null,skyMoon);
                    Field(typeof(ForestCampaign),"next").SetValue(null,0f);ForestCampaign.Update(ref update);
                }
                return;
            }
            throw new Exception(getDescription());
        } catch(Exception ex){SdtdConsole.Instance.Output("[Integrated] FAIL "+ex);}
        finally {
            ForestHordeContext.Inside=false;ForestHordeContext.First=false;ForestHordeContext.Level=0;
            foreach(int id in spawned)if(w.GetEntity(id)!=null)w.RemoveEntity(id,EnumRemoveEntityReason.Despawned);
            if(player!=null){w.Entities.Remove(player.entityId);w.Players.Remove(player.entityId);UnityEngine.Object.Destroy(player.gameObject);}
        }
    }
}
