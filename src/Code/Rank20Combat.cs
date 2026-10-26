using System;using System.Runtime.CompilerServices;using HarmonyLib;using UnityEngine;
namespace Delve {
 public static class Rank20 {
  public sealed class State {public Vector3 Anchor;public bool Anchored;public float StationarySince,LastHostile,BraceUntil,BraceNext,FleetUntil,FleetNext;public bool Ward;}
  public static readonly ConditionalWeakTable<EntityAlive,State> States=new ConditionalWeakTable<EntityAlive,State>();
  public static bool Has(EntityAlive p,string skill,string perk){return p!=null&&p.Progression!=null&&ProgressionRuntime.Has(p,skill,perk);}
  public static bool Armor(EntityAlive p,string tag){if(p==null||p.equipment==null)return false;int count=0;foreach(var item in p.equipment.GetArmor())if(item!=null&&item.ItemClass!=null&&item.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse(tag)))count++;return count>=3;}
  public static string Skill(ItemValue item){return item==null||item.ItemClass==null?null:ProficiencyRules.Identify(item.ItemClass.GetItemName());}
  public static bool Unaware(EntityAlive target,EntityAlive attacker){return target!=null&&!target.IsAlert&&target.GetAttackTarget()==null&&target.GetRevengeTarget()==null;}
  public static bool Staggered(EntityAlive target){return target.emodel!=null&&(target.emodel.IsRagdollActive||(target.emodel.avatarController!=null&&target.emodel.avatarController.IsAnimationHitRunning()));}
  public static void Tick(EntityPlayerLocal p){
   if(!CharacterProgression.IsLocal(p))return;var s=States.GetOrCreateValue(p);
   if(!s.Anchored)s.LastHostile=Time.time;
   if(!s.Anchored||p.IsDead()||(p.position-s.Anchor).sqrMagnitude>.25f){s.Anchor=p.position;s.StationarySince=Time.time;s.Anchored=true;}
   if(p.IsDead()){s.BraceUntil=0;s.FleetUntil=0;}
   bool light=Has(p,"LightArmor","WovenWard")&&Armor(p,"lightArmor");
   if(!light||p.IsDead()){s.Ward=false;s.LastHostile=Time.time;}else if(Rank20Rules.WardReady(light,true,Time.time,s.LastHostile))s.Ward=true;
   CharacterProgression.Set(p,"delveWovenWardReady",s.Ward?1:0);
  }
  public static float Stagger(EntityAlive p,string skill,bool heavy){
   float bonus=0;if(skill=="Unarmed"&&heavy&&Has(p,"Unarmed","PressurePoints"))bonus=.2f;
   if(skill=="Polearms"&&heavy&&Has(p,"Polearms","SetYourFeet")){var s=States.GetOrCreateValue(p);if(s.Anchored&&(p.position-s.Anchor).sqrMagnitude<=.25f&&Time.time-s.StationarySince>=1)bonus=.25f;}
   if(skill=="Staffs"&&Has(p,"Staffs","ShockFront"))bonus=.25f;
   if((skill=="Blades"||skill=="Blunt"||skill=="Polearms"||skill=="Unarmed")&&CharacterProgression.Get(p,"delvePackedLoad")>=.5f&&Has(p,"PackMule","HeavyMomentum"))bonus+=.1f;
   return 1+bonus;
  }
  public static float Healing(EntityAlive p){return Has(p,"Totems","MendingCurrent")?1.15f:1;}
 }
 [HarmonyPatch(typeof(EntityPlayerLocal),"OnUpdateLive")]
 public static class Rank20Tick {static void Postfix(EntityPlayerLocal __instance){Rank20.Tick(__instance);}}
 [HarmonyPatch(typeof(EntityAlive),"DamageEntity",new Type[]{typeof(DamageSource),typeof(int),typeof(bool),typeof(float)})]
 public static class Rank20Contact {
  public struct Context {public EntityPlayerLocal Caster;public string Skill;public bool Heavy;public int Before;public EntityPlayerLocal Receiver;public int ReceiverBefore;public bool WardUsed;}
  [HarmonyPriority(Priority.High)]
  static void Prefix(EntityAlive __instance,DamageSource __0,ref int __1,out Context __state){
   __state=new Context();if(__0==null||__1<=0||__instance.IsDead())return;
   var attacker=__instance.world.GetEntity(__0.getEntityId()) as EntityAlive;
   if(CharacterProgression.IsLocal(__instance)&&attacker!=null&&attacker!=__instance&&attacker.EntityClass.bIsEnemyEntity){
    var state=Rank20.States.GetOrCreateValue(__instance);float reduction=0;__state.Receiver=(EntityPlayerLocal)__instance;__state.ReceiverBefore=__instance.Health;
    if(state.Ward&&Rank20.Has(__instance,"LightArmor","WovenWard")&&Rank20.Armor(__instance,"lightArmor")){__state.WardUsed=true;reduction=.15f;}
    var kind=__0.GetDamageType();bool physical=kind==EnumDamageTypes.Piercing||kind==EnumDamageTypes.Slashing||kind==EnumDamageTypes.Bashing||kind==EnumDamageTypes.Crushing;
    if(physical&&Time.time<state.BraceUntil)reduction=1-(1-reduction)*.9f;
    __1=Math.Max(1,(int)Math.Round(__1*(1-reduction)));
   }
   var p=attacker as EntityPlayerLocal;if(!CharacterProgression.IsLocal(p)||__0.AttackingItem==null||__instance is EntityPlayer)return;
   string skill=Rank20.Skill(__0.AttackingItem);if(skill==null)return;
   var swing=FirstTierCombat.Current;bool heavy=swing!=null&&swing.Player==p&&swing.Heavy;
   float bonus=0;bool unaware=Rank20.Unaware(__instance,p);
   if((skill=="Blades"||skill=="Blunt"||skill=="Polearms"||skill=="Unarmed")&&CharacterProgression.Get(p,"delvePackedLoad")>=.5f&&Rank20.Has(p,"PackMule","HeavyMomentum"))bonus+=.1f;
   if(Rank20.Has(p,"Stealth","OpeningStrike")&&unaware)bonus+=.2f;
   if(skill=="Blades"){
    if(heavy&&Rank20.Has(p,skill,"PowerfulCuts"))bonus+=.2f;
    if(Rank20.Has(p,skill,"ExploitOpening")&&(unaware||Rank20.Staggered(__instance)))bonus+=.2f;
   }
   if(skill=="Blunt"&&heavy&&Rank20.Has(p,skill,"Breaker")&&EffectManager.GetValue(PassiveEffects.PhysicalDamageResist,null,0,__instance)>0)bonus+=.2f;
   if(skill=="Polearms"&&Rank20.Has(p,skill,"PointControl")){
    float reach=EffectManager.GetValue(PassiveEffects.MaxRange,__0.AttackingItem,0,p);Vector3 impact=__0.getHitTransformPosition();
    // Native hit metadata is used; no center-distance or currently held weapon fallback.
    if(impact!=Vector3.zero&&Rank20Rules.LongRange(Vector3.Distance(p.GetLookRay().origin,impact),reach))bonus+=.2f;
   }
   if(skill=="Archery"&&Rank20.Has(p,skill,"Anatomist")&&(__0.GetEntityDamageBodyPart(__instance)&(EnumBodyPartHit.Head|EnumBodyPartHit.Special))!=0)bonus+=.2f;
   if(skill=="Wands"&&Rank20.Has(p,skill,"MeasuredBolt"))bonus+=.1f;
   if(skill=="Staffs"){if(Rank20.Has(p,skill,"Overload"))bonus+=.15f;if(Rank20.Has(p,skill,"FocusedImpact"))bonus+=.15f;}
   __1=Math.Max(1,(int)Math.Round(__1*(1+bonus)));__state=new Context{Caster=p,Skill=skill,Heavy=heavy,Before=__instance.Health};
  }
  static void Postfix(EntityAlive __instance,Context __state){
   if(__state.Receiver!=null&&__instance.Health<__state.ReceiverBefore){var incoming=Rank20.States.GetOrCreateValue(__state.Receiver);incoming.LastHostile=Time.time;if(__state.WardUsed)incoming.Ward=false;}
   var p=__state.Caster;if(p==null||__instance.Health>=__state.Before)return;var s=Rank20.States.GetOrCreateValue(p);
   if(__state.Skill=="Blunt"&&__state.Heavy&&Rank20.Has(p,"Blunt","Brace")&&Time.time>=s.BraceNext){s.BraceUntil=Time.time+3;s.BraceNext=Time.time+6;}
   if(__state.Skill=="Unarmed"&&Rank20.Has(p,"Unarmed","FleetFoot")&&Time.time>=s.FleetNext){s.FleetUntil=Time.time+3;s.FleetNext=Time.time+5;}
  }
 }
 [HarmonyPatch(typeof(EffectManager),"GetValue")]
 public static class Rank20PassiveEffects {
  static void Postfix(PassiveEffects __0,ItemValue __1,EntityAlive __3,FastTags<TagGroup.Global> __5,ref float __result){
   if(__0!=PassiveEffects.PhysicalDamageResist&&__0!=PassiveEffects.StaminaMax&&__0!=PassiveEffects.StaminaChangeOT&&__0!=PassiveEffects.AttacksPerMinute&&__0!=PassiveEffects.RoundsPerMinute&&__0!=PassiveEffects.ReloadSpeedMultiplier&&__0!=PassiveEffects.WalkSpeed&&__0!=PassiveEffects.RunSpeed&&__0!=PassiveEffects.CrouchSpeed)return;
   if(!CharacterProgression.IsLocal(__3))return;var p=(EntityPlayerLocal)__3;
   string skill=Rank20.Skill(__1),name=__1==null||__1.ItemClass==null?"":__1.ItemClass.GetItemName();
   bool heavy=Rank20.Armor(p,"heavyArmor"),medium=Rank20.Armor(p,"mediumArmor"),light=Rank20.Armor(p,"lightArmor");
   if(__0==PassiveEffects.PhysicalDamageResist){if(heavy&&Rank20.Has(p,"HeavyArmor","ReinforcedPlating"))__result+=10;if(medium&&Rank20.Has(p,"MediumArmor","ReinforcedSeams"))__result+=6;}
   if(__0==PassiveEffects.StaminaMax&&heavy&&Rank20.Has(p,"HeavyArmor","DeepReserves"))__result+=20;
   if(__0==PassiveEffects.StaminaChangeOT&&__result<0&&__5.Test_AnySet(FastTags<TagGroup.Global>.Parse("running"))&&!p.CalcIfSwimming()&&medium&&Rank20.Has(p,"MediumArmor","EasyStride"))__result*=.9f;
   if(__0==PassiveEffects.AttacksPerMinute){
    bool primary=__5.Test_AnySet(FastTags<TagGroup.Global>.Parse("primary"))&&!__5.Test_AnySet(FastTags<TagGroup.Global>.Parse("secondary"));
    if(primary&&((skill=="Blunt"&&Rank20.Has(p,skill,"Brawler"))||(skill=="Unarmed"&&Rank20.Has(p,skill,"QuickJabs"))))__result*=1.1f;
   }
   if(__0==PassiveEffects.RoundsPerMinute&&skill=="Wands"&&Rank20.Has(p,skill,"SwiftCasting"))__result*=1.15f;
   if(__0==PassiveEffects.ReloadSpeedMultiplier){
    if(skill=="Archery"&&Rank20.Has(p,skill,name.IndexOf("crossbow",StringComparison.OrdinalIgnoreCase)>=0?"PracticedLoading":"QuickDraw"))__result*=1.15f;
    if((skill=="Wands"||skill=="Staffs"||skill=="Totems"||skill=="Summoning")&&light&&Rank20.Has(p,"LightArmor","OpenChannels"))__result*=1.1f;
   }
   if((__0==PassiveEffects.WalkSpeed||__0==PassiveEffects.RunSpeed||__0==PassiveEffects.CrouchSpeed)&&!p.CalcIfSwimming()){
    float bonus=light&&Rank20.Has(p,"LightArmor","FleetStep")?.05f:0;if(Time.time<Rank20.States.GetOrCreateValue(p).FleetUntil)bonus+=.1f;__result*=1+bonus;
   }
  }
 }
 [HarmonyPatch(typeof(AIDirector),"NotifyNoise")]
 public static class Rank20Footsteps {static void Prefix(Entity __0,string __2,ref float __3){var p=__0 as EntityPlayer;if(p!=null&&__2!=null&&(__2.StartsWith("step",StringComparison.Ordinal)||__2=="player_swim"||__2.StartsWith("playerland",StringComparison.Ordinal))&&Rank20.Has(p,"Stealth","LightTread"))__3*=.85f;}}
 [HarmonyPatch(typeof(EntityAlive),"GetLightBrightness")]
 public static class Rank20Shadowcraft {static void Postfix(EntityAlive __instance,ref float __result){if(__instance is EntityPlayer&&__instance.IsCrouching&&__result<=.35f&&Rank20.Has(__instance,"Stealth","Shadowcraft"))__result*=.85f;}}
}

