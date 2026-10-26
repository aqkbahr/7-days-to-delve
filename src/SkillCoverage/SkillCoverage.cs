using System;
using System.Reflection;
using HarmonyLib;
using UnityEngine;
using Delve;
namespace DelveCoverage {
 public class ModApi:IModApi {public void InitMod(Mod mod){new Harmony("delve.skill.coverage").PatchAll(Assembly.GetExecutingAssembly());for(int i=0;i<ProgressionUiData.Skills.Length;i++){var s=ProgressionUiData.Skills[i];string training=s.Training;var branches=s.Branches;
 if(s.Id=="Alchemy"){training="Craft reagents, medicines and explosive charges; use effective treatment/protection or damage enemies with charges. Powder 10; blast charges 20; excavation charges 40.";branches=new[]{"Apothecary","Restoratives","Arcane & Explosives"};}
 if(s.Id=="Smithing")training="Forge metal equipment; craft a salvage wrench at 20. Salvage metal objects and repair or upgrade metal equipment/structures.";
 if(s.Id=="Carpentry")training="Craft wood and outfitting goods; gather wood; build, upgrade and repair wood structures and equipment.";
 if(s.Id=="Mining")training="Harvest natural deposits and process minerals; build, upgrade and repair stone structures.";
 if(s.Id=="Farming")training="Plant crops and farm plots; harvest crops, wild plants and animal remains.";
 if(s.Id=="Totems")training="Deal totem damage, restore health, or protect a recipient from hostile hits. Repeated ward casting alone gives no practice.";
 ProgressionUiData.Skills[i]=new SkillUiDefinition(s.Id,s.Title,s.Tab,training,branches,s.Perks);
 }}}
 public static class Coverage {
  [ThreadStatic]public static EntityPlayerLocal Actor;
  static EntityPlayerLocal owner;static Rules.Cooldowns limits=new Rules.Cooldowns();
  public static bool Local(EntityAlive p){return CharacterProgression.IsLocal(p)&&!p.IsDead();}
  public static void Credit(EntityPlayerLocal p,string skill,int amount,string key,float delay){if(!Local(p)||amount<=0)return;if(owner!=p){owner=p;limits=new Rules.Cooldowns();}if(limits.Take(key,Time.time,delay))CharacterProgression.Practice(p,skill,amount);}
  public static bool Salvage(ItemValue item,BlockValue block){return item!=null&&item.ItemClass!=null&&item.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse("salvageTool"))&&!block.isair&&!block.isTerrain&&Rules.MaterialSkill(block.Block.blockMaterial.id)=="Smithing";}
  public static string BlockSkill(Block block){return Rules.MaterialSkill(block.blockMaterial.id);}
  public static string ItemSkill(ItemValue item){if(item==null||item.ItemClass==null)return null;string n=item.ItemClass.GetItemName();return TrainingHooks.CraftedSkill(n,"")??Rules.MaterialSkill(item.ItemClass.MadeOfMaterial.id);}
 }
 [HarmonyPatch(typeof(RecipeProgression),"Allowed")]
 public static class ExtraRecipes {static bool Prefix(Recipe recipe,EntityAlive player,ref bool __result){if(recipe==null||recipe.IsScrap)return true;var row=CoverageCatalog.Find(ForestSliceCatalog.Key(recipe));if(row==null)return true;__result=player!=null&&ProficiencyRules.Rank(CharacterProgression.Get(player,"delvePractice"+row.Skill))>=row.Rank;return false;}}
 [HarmonyPatch(typeof(TrainingHooks),"CraftedSkill")]
 public static class ExtraCraftOwners {static void Postfix(string name,ref string __result){var row=CoverageCatalog.ByName(name);if(row!=null)__result=row.Skill;}}
 [HarmonyPatch(typeof(ForestSliceCatalog),"Rank")]
 public static class ExtraRanks {static void Postfix(Recipe r,ref int __result){var row=CoverageCatalog.Find(ForestSliceCatalog.Key(r));if(row!=null)__result=row.Rank;}}
 [HarmonyPatch(typeof(ForestSliceCatalog),"Minimum")]
 public static class ExtraMinimum {static void Postfix(string n,ref int __result){var row=CoverageCatalog.ByName(n);if(row!=null)__result=row.Rank;}}
 [HarmonyPatch(typeof(ForestSliceCatalog),"Skill")]
 public static class ExtraSkills {static void Postfix(string n,ref string __result){var row=CoverageCatalog.ByName(n);if(row!=null)__result=row.Skill;}}
 [HarmonyPatch(typeof(ProficiencyRules),"Identify")]
 public static class ExtraUseOwners {static void Postfix(string itemName,ref string __result){if(Rules.Explosive(itemName))__result="Alchemy";if(itemName=="meleeToolSalvageT1Wrench")__result="Blunt";}}
 [HarmonyPatch(typeof(EntityAlive),"DamageEntity",new Type[]{typeof(DamageSource),typeof(int),typeof(bool),typeof(float)})]
 public static class ExplosiveSkillDamage {static void Prefix(EntityAlive __instance,DamageSource __0,ref int __1){if(__0==null||__0.AttackingItem==null||__0.AttackingItem.ItemClass==null||!Rules.Explosive(__0.AttackingItem.ItemClass.GetItemName()))return;var p=__instance.world.GetEntity(__0.getEntityId()) as EntityAlive;if(p==null||p.Progression==null)return;__1=(int)Math.Round(__1*Rules.ExplosiveMultiplier(ProficiencyRules.Rank(CharacterProgression.Get(p,"delvePracticeAlchemy"))));}}
 [HarmonyPatch(typeof(Explosion),"AttackBlocks")]
 public static class ExcavationPractice {static void Postfix(Explosion __instance,int __0,ItemValue __1){if(__1==null||__1.ItemClass==null||!Rules.Explosive(__1.ItemClass.GetItemName()))return;var world=GameManager.Instance.World;var p=world.GetEntity(__0) as EntityPlayerLocal;if(!Coverage.Local(p))return;int count=0;foreach(var change in __instance.ChangedBlockPositions)if(change.Value.blockValue.isair&&world.GetBlock(change.Key).isTerrain)count++;Coverage.Credit(p,"Alchemy",Math.Min(20,count),"excavation",1);}}
 // Native callbacks occur only after the action has consumed inputs and succeeded.
 [HarmonyPatch(typeof(ItemActionPlaceAsBlock),"ExecuteAction")]
 public static class PlaceContext {static void Prefix(ItemActionData __0,out EntityPlayerLocal __state){__state=Coverage.Actor;Coverage.Actor=__0.invData.holdingEntity as EntityPlayerLocal;}static Exception Finalizer(Exception __exception,EntityPlayerLocal __state){Coverage.Actor=__state;return __exception;}}
 [HarmonyPatch(typeof(BlockToolSelection),"PlaceBlock")]
 public static class ShapeContext {static void Prefix(ItemInventoryData __0,out EntityPlayerLocal __state){__state=Coverage.Actor;Coverage.Actor=__0.holdingEntity as EntityPlayerLocal;}static Exception Finalizer(Exception __exception,EntityPlayerLocal __state){Coverage.Actor=__state;return __exception;}}
 [HarmonyPatch(typeof(ItemActionRepair),"OnHoldingUpdate")]
 public static class UpgradeContext {static void Prefix(ItemActionData __0,out EntityPlayerLocal __state){__state=Coverage.Actor;Coverage.Actor=__0.invData.holdingEntity as EntityPlayerLocal;}static Exception Finalizer(Exception __exception,EntityPlayerLocal __state){Coverage.Actor=__state;return __exception;}}
 [HarmonyPatch(typeof(ItemActionRepair),"ExecuteAction")]
 public static class RepairContext {static void Prefix(ItemActionData __0,out EntityPlayerLocal __state){__state=Coverage.Actor;Coverage.Actor=__0.invData.holdingEntity as EntityPlayerLocal;}static Exception Finalizer(Exception __exception,EntityPlayerLocal __state){Coverage.Actor=__state;return __exception;}}
 [HarmonyPatch(typeof(QuestEventManager),"BlockPlaced")]
 public static class PlacePractice {static void Postfix(string __0,Vector3i __1){var p=Coverage.Actor;if(!Coverage.Local(p))return;var block=Block.GetBlockValue(__0,false).Block;if(block==null)return;bool plant=block is BlockPlant||__0.IndexOf("farmplot",StringComparison.OrdinalIgnoreCase)>=0;Coverage.Credit(p,plant?"Farming":Coverage.BlockSkill(block),plant?4:2,"place:"+__1,60);}}
 [HarmonyPatch(typeof(QuestEventManager),"BlockUpgraded")]
 public static class UpgradePractice {static void Postfix(string __0,Vector3i __1){var p=Coverage.Actor;if(!Coverage.Local(p))return;var block=Block.GetBlockValue(__0,false).Block;string next=block.Properties.GetString("UpgradeBlock","ToBlock");if(!String.IsNullOrEmpty(next))block=Block.GetBlockValue(next,false).Block;Coverage.Credit(p,Coverage.BlockSkill(block),8,"upgrade:"+__1+":"+next,30);}}
 [HarmonyPatch(typeof(Block),"DamageBlock")]
 public static class StructureRepair {static void Postfix(Block __instance,BlockValueRef __1,BlockValue __2,int __3,int __4,int __result){var p=Coverage.Actor;if(!Coverage.Local(p)||p.entityId!=__4||__3>=0||__2.ischild)return;int amount=Rules.RepairCredit(__2.damage,__result);Coverage.Credit(p,Coverage.BlockSkill(__instance),amount,"repair:"+__1,10);}}
 [HarmonyPatch(typeof(QuestEventManager),"RepairedItem")]
 public static class GearRepair {static void Postfix(ItemValue __0){var p=TrainingHooks.Player;if(!Coverage.Local(p)||__0==null)return;Coverage.Credit(p,Coverage.ItemSkill(__0),8,"gearrepair",5);}}
 // Replace the raw-resource fallback for genuine metal salvage, not add two skills.
 [HarmonyPatch]
 public static class SalvagePractice {
  static MethodBase TargetMethod(){return AccessTools.Method(typeof(HarvestPractice),"Postfix");}
  static bool Prefix(ItemValue __0,ItemStack __1,BlockValue __2){if(!Coverage.Salvage(__0,__2))return true;var action=HarvestContext.Action;if(action==null||action.indexInEntityOfAction!=0)return true;var p=action.invData.holdingEntity as EntityPlayerLocal;if(!Coverage.Local(p)||__1==null||__1.count<=0)return true;Coverage.Credit(p,"Smithing",Math.Min(10,Math.Max(1,__1.count/2)),"salvage",1);return false;}
 }
 [HarmonyPatch(typeof(ItemActionAttack),"GetDamageBlock")]
 public static class SalvageEfficiency {static void Postfix(ItemValue __0,BlockValue __1,EntityAlive __2,ref float __result){if(__2!=null&&Coverage.Salvage(__0,__1))__result*=1+.0025f*(ProficiencyRules.Rank(CharacterProgression.Get(__2,"delvePracticeSmithing"))-1);}}
 [HarmonyPatch(typeof(EntityAlive),"DamageEntity",new Type[]{typeof(DamageSource),typeof(int),typeof(bool),typeof(float)})]
 public static class ProtectivePractice {
  public struct Hit {public int Before;public EntityPlayerLocal Ward,Alchemy;}
  static void Prefix(EntityAlive __instance,DamageSource __0,int __1,out Hit __state){__state=new Hit();if(__0==null||__1<=0||__instance.IsDead()||!__0.AffectedByArmor())return;var enemy=__instance.world.GetEntity(__0.getEntityId()) as EntityAlive;if(enemy==null||enemy==__instance||!enemy.EntityClass.bIsEnemyEntity)return;__state.Before=__instance.Health;var ward=__instance.Buffs.GetBuff("delveProtectiveWard");if(ward!=null)__state.Ward=__instance.world.GetEntity(ward.InstigatorId) as EntityPlayerLocal;var draught=__instance.Buffs.GetBuff("delveWard");var kind=__0.GetDamageType();bool physical=kind==EnumDamageTypes.Piercing||kind==EnumDamageTypes.Slashing||kind==EnumDamageTypes.Bashing||kind==EnumDamageTypes.Crushing;if(draught!=null&&physical)__state.Alchemy=__instance.world.GetEntity(draught.InstigatorId) as EntityPlayerLocal;}
  static void Postfix(EntityAlive __instance,Hit __state){if(__state.Before<=__instance.Health)return;Coverage.Credit(__state.Ward,"Totems",4,"ward:"+__instance.entityId,5);Coverage.Credit(__state.Alchemy,"Alchemy",4,"draught:"+__instance.entityId,5);}
 }
 [HarmonyPatch(typeof(EntityAlive),"FireEvent",new Type[]{typeof(MinEventTypes),typeof(bool)})]
 public static class InjuryTreatment {
  static readonly string[] injuries={"buffLegSprained","buffLegBroken","buffArmSprained","buffArmBroken"};
  public struct State {public EntityAlive Target;public int Mask;}
  static void Prefix(EntityAlive __instance,MinEventTypes __0,out State __state){__state=new State();if(!Coverage.Local(__instance)||(__0!=MinEventTypes.onSelfPrimaryActionEnd&&__0!=MinEventTypes.onSelfSecondaryActionEnd))return;var ctx=__instance.MinEventContext;if(ctx==null||ctx.ItemValue==null||ctx.ItemValue.ItemClass==null)return;string n=ctx.ItemValue.ItemClass.GetItemName();if(n!="medicalSplint"&&n!="medicalPlasterCast")return;__state.Target=__0==MinEventTypes.onSelfPrimaryActionEnd?__instance:ctx.Other;if(__state.Target==null)return;for(int i=0;i<injuries.Length;i++)if(__state.Target.Buffs.HasBuff(injuries[i]))__state.Mask|=1<<i;}
  static void Postfix(EntityAlive __instance,State __state){if(__state.Target==null||__state.Mask==0)return;for(int i=0;i<injuries.Length;i++)if((__state.Mask&(1<<i))!=0&&!__state.Target.Buffs.HasBuff(injuries[i])){Coverage.Credit((EntityPlayerLocal)__instance,"Alchemy",12,"treatment:"+__state.Target.entityId,10);break;}}
 }
 [HarmonyPatch(typeof(EntityPlayerLocal),"OnUpdateLive")]
 public static class EnvironmentalProtection {
  static float next;static EntityPlayerLocal owner;
  static void Postfix(EntityPlayerLocal __instance){if(!Coverage.Local(__instance))return;if(owner!=__instance){owner=__instance;next=Time.time+30;}if(Time.time<next)return;next=Time.time+30;if(!__instance.Buffs.HasBuff("delveArborProtected"))return;var biome=__instance.world.GetBiomeInWorld((int)__instance.position.x,(int)__instance.position.z);if(biome!=null&&biome.m_sBiomeName=="burnt_forest")Coverage.Credit(__instance,"Alchemy",1,"arbor-protection",30);}
 }
}
