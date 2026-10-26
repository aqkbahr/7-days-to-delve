using System;using HarmonyLib;using UnityEngine;
namespace Delve {
 [HarmonyPatch(typeof(EntityAlive),"damageEntityLocal")]
 public static class Rank20StaggerScope {
  [ThreadStatic]public static float Current;
  public static float Multiplier {get{return Current>0?Current:1;}}
  static void Prefix(EntityAlive __instance,DamageSource __0,out float __state){
   __state=Current;Current=1;if(__0==null||__0.AttackingItem==null)return;
   var p=__instance.world.GetEntity(__0.getEntityId()) as EntityPlayerLocal;if(!CharacterProgression.IsLocal(p))return;
   var swing=FirstTierCombat.Current;Current=Rank20.Stagger(p,Rank20.Skill(__0.AttackingItem),swing!=null&&swing.Player==p&&swing.Heavy);
  }
  static Exception Finalizer(Exception __exception,float __state){Current=__state;return __exception;}
 }
 [HarmonyPatch(typeof(vp_FPController),"UpdateThrottleWalk")]
 public static class Rank20Walking {
  public struct Before {public float Acceleration,Backward;}
  static void Prefix(vp_FPController __instance,out Before __state){
   __state=new Before{Acceleration=__instance.MotorAcceleration,Backward=__instance.MotorBackwardsSpeed};var p=__instance.localPlayer;
   if(!CharacterProgression.IsLocal(p)||p.IsDead()||p.AttachedToEntity!=null||p.IsSwimming())return;
   string skill=Rank20.Skill(p.inventory.holdingItemItemValue);
   if(!p.IsRunning&&skill=="Polearms"&&Rank20.Has(p,skill,"ClearSpace"))__instance.MotorBackwardsSpeed=Math.Min(1,__instance.MotorBackwardsSpeed*1.1f);
   if(!p.AimingGun)return;
   float bonus=skill=="Wands"&&Rank20.Has(p,skill,"AgileFocus")?.15f:0;
   if(Rank20.Armor(p,"mediumArmor")&&Rank20.Has(p,"MediumArmor","ReadyFootwork"))bonus+=.1f;
   if(bonus<=0)return;
   // Read the baseline without CalculateMaxSpeed: that method resets all motor
   // presets and restores state flags without restoring their applied values.
   float normal=0;foreach(var state in __instance.States)if(state.Name=="Default"&&state.Preset!=null){
    object acceleration=state.Preset.GetFieldValue("MotorAcceleration"),damping=state.Preset.GetFieldValue("MotorDamping");
    if(acceleration is float&&damping is float&&(float)damping>0)normal=(float)acceleration*6/(float)damping;break;
   }
   if(normal<=0)return;float current=__state.Acceleration*6/Math.Max(.0001f,__instance.MotorDamping);
   __instance.MotorAcceleration=__state.Acceleration*(current>0?Rank20Rules.CappedMovement(current,normal,bonus)/current:1);
  }
  static Exception Finalizer(vp_FPController __instance,Exception __exception,Before __state){__instance.MotorAcceleration=__state.Acceleration;__instance.MotorBackwardsSpeed=__state.Backward;return __exception;}
 }
 [HarmonyPatch(typeof(EntityPlayerLocal),"SwimModeUpdateThrottle")]
 public static class Rank20Swimming {
  public struct Before {public bool Active;public Vector3 Native;}
  static void Prefix(EntityPlayerLocal __instance,out Before __state){
   __state=new Before();if(!CharacterProgression.IsLocal(__instance)||!__instance.IsSwimming()||__instance.vp_FPController==null||!Rank20.Has(__instance,"Athletics","StrongStroke"))return;
   __state.Active=true;__state.Native=__instance.vp_FPController.m_MotorThrottle;
   // Work in native-speed coordinates; do not compound a multiplier every frame.
   __instance.vp_FPController.m_MotorThrottle=__state.Native/1.15f;
  }
  static Exception Finalizer(EntityPlayerLocal __instance,Exception __exception,Before __state){if(__state.Active){if(__exception!=null)__instance.vp_FPController.m_MotorThrottle=__state.Native;else {var v=__instance.vp_FPController.m_MotorThrottle;float climb=v.y;v*=1.15f;if(__instance.swimClimbing)v.y=climb;__instance.vp_FPController.m_MotorThrottle=v;}}return __exception;}
 }
}
