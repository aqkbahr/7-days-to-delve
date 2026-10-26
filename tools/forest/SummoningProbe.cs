using System;using System.Collections.Generic;using System.Reflection;using HarmonyLib;using UnityEngine;using Delve;
public class ConsoleCmdSummoningProbe:ConsoleCmdAbstract
{
 static int checks,practice,kills;static void Check(bool b,string s){checks++;if(!b)throw new Exception(s);}
 static bool KillCredit(){kills++;return false;}
 static bool Credit(EntityPlayer owner,int amount){practice+=amount;return false;}
 public override string[] getCommands(){return new[]{"summoningverify"};}
 public override string getDescription(){return "Native summoning content, combat and lifetime fixture.";}
 public override void Execute(List<string> args,CommandSenderInfo sender){var spawned=new List<EntityAlive>();var world=GameManager.Instance.World;var h=new Harmony("delve.summon.probe");bool old=XUiM_Recipes.WorkstationCrafting;var backpack=XUiM_Recipes.BackpackCrafting;try{
  checks=practice=kills=0;h.Patch(AccessTools.Method(typeof(EntityPlayer),"AddKillXP"),new HarmonyMethod(AccessTools.Method(typeof(ConsoleCmdSummoningProbe),"KillCredit")));h.Patch(AccessTools.Method(typeof(Summoning),"Practice"),new HarmonyMethod(AccessTools.Method(typeof(ConsoleCmdSummoningProbe),"Credit")));
  XUiM_Recipes.WorkstationCrafting=true;XUiM_Recipes.BackpackCrafting=(BackpackCraftingOptions)1;
  var owner=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),new Vector3(0,200,0)) as EntityPlayer;owner.world=world;world.Entities.Add(owner.entityId,owner);spawned.Add(owner);
  Check(Array.IndexOf(ProficiencyRules.Skills,"Summoning")>=0,"Summoning skill registered");Check(ProficiencyRules.Identify("delveSummoningRod")=="Summoning"&&ProficiencyRules.Identify("delveSummoningRune")=="Summoning","Rod/rune skill identity");
  var rod=ItemClass.GetItem("delveSummoningRod",false);rod.Quality=1;rod.Stats=new ItemValue.Stat[0];Check(rod.ItemClass.Actions[0] is ItemActionRanged,"Native ranged action");Check(EffectManager.GetValue(PassiveEffects.MagazineSize,rod)==1,"One-rune magazine");Check(EffectManager.GetValue(PassiveEffects.EntityDamage,rod)==0,"No damaging cast ray");
  int recipes=0;foreach(var recipe in CraftingManager.GetAllRecipes())if(recipe.GetName()=="delveSummoningRod"||recipe.GetName()=="delveSummoningRune"){
   recipes++;Check(!XUiM_Recipes.FilterRecipesByWorkstation("",CraftingManager.GetAllRecipes()).Contains(recipe),"Inventory excluded");Check(recipe.craftingToolType==0,"No station add-on requirement");Check(RecipeProgression.Allowed(recipe,owner)&&recipe.IsUnlocked(owner),"Starter recipe access");
   var te=new TileEntityWorkstation((Chunk)null);te.SetDisableModifiedCheck(true);te.Queue=new[]{new RecipeQueueItem{Recipe=recipe,Multiplier=1,CraftingTimeLeft=0,OneItemCraftTime=1,Quality=1,StartingEntityId=-1}};AccessTools.Method(typeof(TileEntityWorkstation),"HandleRecipeQueue").Invoke(te,new object[]{2f});int output=0;foreach(var s in te.Output)if(s.itemValue.type==recipe.itemValueType)output+=s.count;Check(output==recipe.count,"Native crafting output");
  }Check(recipes==3,"Three recipe routes");
  var body=Summoning.Spawn(owner,new Vector3(0,200,2));spawned.Add(body);Check(body!=null&&body.OwnerId==owner.entityId,"Server-owned boar spawn");Check(Math.Abs(body.Expires-Time.time-60)<.1f,"60 second lifetime");Check(body.Health==80&&body.GetMaxHealth()==80,"Weak starter health");Check(!body.IsSavedToFile(),"No persisted summon bodies");Check(!body.EntityClass.bIsEnemyEntity,"Allied entity");
  var enemy=EntityFactory.CreateEntity(EntityClass.FromString("delveCorruptedWalker"),new Vector3(0,200,3)) as EntityAlive;enemy.world=world;world.Entities.Add(enemy.entityId,enemy);spawned.Add(enemy);
  Check(Summoning.Hostile(enemy)&&!Summoning.Hostile(owner)&&!Summoning.Hostile(body),"Hostility exclusions");
  body.SetAttackTarget(enemy,200);enemy.SetAttackTarget(body,200);
  var boarAI=new EAIApproachAndAttackTarget();boarAI.Init(body);boarAI.SetData(new Dictionary<string,string>{{"class","EntityZombie,0,EntityEnemyAnimal,0"}});Check(boarAI.CanExecute(),"Native boar melee accepts hostile target");
  var enemyAI=new EAIApproachAndAttackTarget();enemyAI.Init(enemy);enemyAI.SetData(new Dictionary<string,string>{{"class","EntityPlayer,0"}});Check(enemyAI.CanExecute(),"Native enemy melee accepts allied summon");
  int hp=enemy.Health;var damage=new DamageSourceEntity(EnumDamageSource.External,EnumDamageTypes.Bashing,body.entityId);damage.SetIgnoreConsecutiveDamages(true);enemy.DamageEntity(damage,99,false,0);Check(enemy.Health<hp&&hp-enemy.Health<=6,"Actual native summon damage bounded");Check(practice==hp-enemy.Health,"Practice only actual damage");
  hp=owner.Health;owner.DamageEntity(damage,99,false,0);Check(owner.Health==hp,"Summon cannot hurt player");
  hp=body.Health;var hostile=new DamageSourceEntity(EnumDamageSource.External,EnumDamageTypes.Bashing,enemy.entityId);hostile.SetIgnoreConsecutiveDamages(true);body.DamageEntity(hostile,10,false,0);Check(body.Health<hp,"Enemy damages summon");
  hp=body.Health;var friendly=new DamageSourceEntity(EnumDamageSource.External,EnumDamageTypes.Bashing,owner.entityId);friendly.SetIgnoreConsecutiveDamages(true);body.DamageEntity(friendly,10,false,0);Check(body.Health==hp,"Owner cannot farm summon");
  var victim=EntityFactory.CreateEntity(EntityClass.FromString("delveCorruptedWalker"),new Vector3(0,200,4)) as EntityAlive;victim.world=world;world.Entities.Add(victim.entityId,victim);spawned.Add(victim);victim.Health=1;
  victim.DamageEntity(damage,99,false,0);SdtdConsole.Instance.Output("SUMMON KILL HP "+victim.Health+" dead="+victim.IsDead()+" credits="+kills);Check(kills==1,"Summon kill credits owner XP once");victim.DamageEntity(damage,99,false,0);Check(kills==1,"Dead target cannot repeat kill XP");
  int id=body.entityId;var replacement=Summoning.Spawn(owner,new Vector3(0,200,2));spawned.Add(replacement);Check(world.GetEntity(id)==null,"Replacement removes old summon");
  replacement.Expires=Time.time;Summoning.Tick();Check(world.GetEntity(replacement.entityId)==null,"Timer expiry despawns");
  CharacterProgression.Set(owner,"delvePracticeSummoning",ProficiencyRules.Threshold(20));body=Summoning.Spawn(owner,new Vector3(0,200,2));spawned.Add(body);SdtdConsole.Instance.Output("SUMMON RANK "+body.Rank+" HP "+body.Health+" MAX "+body.GetMaxHealth());Check(body.Health==118&&body.GetMaxHealth()==118&&SummonRules.Damage(body.Rank)==7,"Rank20 scaling");int corrupted=Core.Progress.CorruptedKills;body.Health=1;body.DamageEntity(hostile,10,false,0);Check(body.IsDead()&&Core.Progress.CorruptedKills==corrupted,"Summon death cannot farm campaign kills");
  var wild=EntityFactory.CreateEntity(EntityClass.FromString("animalBoar"),new Vector3(0,200,5)) as EntityAlive;wild.world=world;spawned.Add(wild);Check(Summoning.Hostile(wild),"Hostile native boars recognized despite safe-zone flag");
  body=Summoning.Spawn(owner,new Vector3(0,200,2));spawned.Add(body);owner.Health=0;Summoning.Tick();Check(world.GetEntity(body.entityId)==null,"Owner death cleanup");
  Check(SummonRules.Health(1)==80&&SummonRules.Health(20)==118&&SummonRules.Health(1000)==278,"Health clamps");Check(SummonRules.Health(1,6)==120&&SummonRules.Damage(1,6)==9,"Rod quality scales companion stats");Check(!SummonRules.Expired(59,60,true,true)&&SummonRules.Expired(60,60,true,true),"Exact duration boundary");
  SdtdConsole.Instance.Output("[Summoning] PASS "+checks+" native content, recipes, spawn, replacement, damage, friendly exclusion, practice credit, scaling and cleanup checks. Live input/pathfinding and remote client remain separate acceptance.");
 }catch(Exception e){SdtdConsole.Instance.Output("[Summoning] FAIL "+e);}finally{h.UnpatchSelf();XUiM_Recipes.WorkstationCrafting=old;XUiM_Recipes.BackpackCrafting=backpack;foreach(var e in spawned)if(e!=null){world.RemoveEntity(e.entityId,EnumRemoveEntityReason.Despawned);if(e!=null&&e.gameObject!=null)UnityEngine.Object.Destroy(e.gameObject);}Summoning.Reset();}}
}

