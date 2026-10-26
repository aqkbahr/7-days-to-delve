using System;using System.Collections.Generic;using HarmonyLib;using UnityEngine;
namespace DelvePresentation {
 public static class ForestEffects {
  public static int Active,Spawned,Dropped;public const int Limit=64;
  public static GameObject Spawn(string name,Vector3 absolute,Transform parent=null,bool loop=false){
   if(SystemInfo.graphicsDeviceType==UnityEngine.Rendering.GraphicsDeviceType.Null)return null;
   var player=GameManager.Instance.World==null?null:GameManager.Instance.World.GetPrimaryPlayer();if(player==null||(player.position-absolute).sqrMagnitude>2500||Active>=Limit){Dropped++;return null;}
   try{var go=UnityEngine.Object.Instantiate(ModApi.Prefab("forestweapons",name),absolute-Origin.position,Quaternion.identity);if(parent!=null)go.transform.SetParent(parent,true);go.name="DelveEffect_"+name;
    foreach(var ps in go.GetComponentsInChildren<ParticleSystem>(true)){ps.Stop(true,ParticleSystemStopBehavior.StopEmittingAndClear);var main=ps.main;main.loop=loop;main.stopAction=loop?ParticleSystemStopAction.None:ParticleSystemStopAction.Destroy;main.maxParticles=Math.Min(128,main.maxParticles);ps.Play();}
    Active++;Spawned++;go.AddComponent<EffectLease>();if(!loop)UnityEngine.Object.Destroy(go,8);return go;
   }catch(Exception ex){Log.Warning("[ForestArt] Effect unavailable "+name+": "+ex.Message);return null;}
  }
  public static string Family(ItemValue item){
   if(item==null||item.ItemClass==null)return null;string name=item.ItemClass.GetItemName();string[] e;if(HeldCatalog.Items.TryGetValue(name,out e))return e[1];
   // Projectile damage carries the ammunition item, not necessarily its launcher.
   switch(name){case "delveWandRune":case "delveMooncapWandRune":case "delveEtchedWandRune":return "wand";case "delveStaffRune":case "delveMooncapStaffRune":case "delveEtchedStaffRune":return "staff";case "ammoArrowStone":case "ammoArrowIron":case "ammoCrossbowBoltStone":case "ammoCrossbowBoltIron":return "bow";}
   return null;
  }
  public static void Cast(ItemActionData data){if(data==null||data.invData==null)return;var owner=data.invData.holdingEntity;if(owner==null)return;string kind=Family(data.invData.itemValue);string fx=kind=="wand"?"fxSparkCast":kind=="staff"?"fxEmberCast":kind=="hex"?"fxHexCast":kind=="heal"?"fxHealCast":kind=="ward"?"fxWardCast":null;if(fx==null)return;
   var held=data.invData.model==null?null:data.invData.model.GetComponent<HeldVisual>();var socket=held==null?null:held.EffectOrigin;Vector3 pos=socket==null?owner.GetLookRay().origin+owner.GetLookRay().direction*.4f:socket.position+Origin.position;Spawn(fx,pos,socket);
  }
 }
 public class EffectLease:MonoBehaviour {void OnDestroy(){ForestEffects.Active=Math.Max(0,ForestEffects.Active-1);}}
 [HarmonyPatch(typeof(ItemActionDynamicMelee),"ExecuteAction")]
 public static class MeleeSweepVisual {
  static void Prefix(ItemActionData __0,out bool __state){var data=__0 as ItemActionDynamicMelee.ItemActionDynamicMeleeData;__state=data!=null&&data.Attacking;}
  static void Postfix(ItemActionData __0,bool __state){var data=__0 as ItemActionDynamicMelee.ItemActionDynamicMeleeData;if(data==null||__state||!data.Attacking)return;string family=ForestEffects.Family(data.invData.itemValue);if(family!="dagger"&&family!="mace"&&family!="spear"&&family!="wraps")return;var held=data.invData.model==null?null:data.invData.model.GetComponent<HeldVisual>();if(held!=null&&held.EffectOrigin!=null)ForestEffects.Spawn("fxMeleeSweep",held.EffectOrigin.position+Origin.position,held.EffectOrigin);}
 }
 [HarmonyPatch(typeof(ProjectileMoveScript),"Fire")]
 public static class ArrowTrailVisual {
  static void Postfix(ProjectileMoveScript __instance){string family=ForestEffects.Family(__instance.itemValueLauncher);if(family!="bow"&&family!="crossbow")return;var trail=__instance.GetComponent<ProjectileTrail>();if(trail==null)trail=__instance.gameObject.AddComponent<ProjectileTrail>();trail.Begin();}
 }
 public class ProjectileTrail:MonoBehaviour {
  GameObject effect;ProjectileMoveScript projectile;
  public void Begin(){End();projectile=GetComponent<ProjectileMoveScript>();effect=ForestEffects.Spawn("fxArrowTrail",transform.position+Origin.position,transform,true);}
  void Update(){if(projectile==null||projectile.state!=ProjectileMoveScript.State.Active){End();return;}var p=GameManager.Instance.World.GetPrimaryPlayer();if(p==null||(p.position-(transform.position+Origin.position)).sqrMagnitude>2500)End();}
  void End(){if(effect!=null)Destroy(effect);effect=null;}
  void OnDisable(){End();}
  void OnDestroy(){End();}
 }
 [HarmonyPatch(typeof(MinEventActionModifyStats),"execute")]
 public static class HealingPulseVisual {
  static void Prefix(MinEventParams __0,out int __state){__state=__0!=null&&__0.Self!=null&&__0.Buff!=null&&__0.Buff.BuffName.StartsWith("delveHealPulse",StringComparison.Ordinal)?__0.Self.Health:-1;}
  static void Postfix(MinEventParams __0,int __state){if(__state>=0&&__0.Self.Health>__state)ForestEffects.Spawn("fxHealPulse",__0.Self.position+Vector3.up,__0.Self.transform);}
 }
 // This native callback is reached by both successful local shots and network
 // action-effect replay. Dry fire and trigger release do not call it.
 [HarmonyPatch(typeof(ItemActionRanged),"onHoldingEntityFired")]
 public static class CastVisual {static void Postfix(ItemActionData __0){ForestEffects.Cast(__0);}}
 // Superseded by the continuous gem recharge in DelveBatch10; keep no completion burst.
 public static class RechargeVisual {
  static void Prefix(ItemActionRanged.ItemActionDataRanged __0,out int __state){__state=__0==null?-1:__0.invData.itemValue.Meta;}
  static void Postfix(ItemActionRanged.ItemActionDataRanged __0,int __state){if(__0==null||__0.invData.itemValue.Meta<=__state)return;var family=ForestEffects.Family(__0.invData.itemValue);if(family=="wand"||family=="staff"||family=="hex"||family=="heal"||family=="ward")ForestEffects.Spawn("fxRecharge",__0.invData.holdingEntity.position+Vector3.up,__0.invData.holdingEntity.transform);}
 }
 [HarmonyPatch(typeof(EntityAlive),"DamageEntity",new Type[]{typeof(DamageSource),typeof(int),typeof(bool),typeof(float)})]
 public static class ImpactVisual {
  static void Prefix(EntityAlive __instance,out int __state){__state=__instance.Health;}
  static void Postfix(EntityAlive __instance,DamageSource __0,int __state){if(__0==null||__instance.Health>=__state)return;string family=ForestEffects.Family(__0.AttackingItem);string fx=family=="wand"?"fxSparkImpact":family=="staff"?"fxEmberImpact":family=="dagger"?"fxBladeImpact":family=="mace"||family=="wraps"?"fxBluntImpact":family=="spear"?"fxThrustImpact":family=="bow"||family=="crossbow"?"fxArrowImpact":null;if(fx!=null)ForestEffects.Spawn(fx,__instance.position+Vector3.up,__instance.transform);}
 }
 public class BuffVisuals:MonoBehaviour {
  EntityAlive owner;float next;readonly Dictionary<string,GameObject> active=new Dictionary<string,GameObject>();
  static readonly string[] Buffs={"delveProtectiveWard","delveTotemDecay","delveStaffBurst","delveMendingGlow"};
  static readonly string[] Effects={"fxWardStatus","fxHexStatus","fxEmberBurst","fxHealPulse"};
  void Awake(){owner=GetComponent<EntityAlive>();}
  void Update(){if(Time.time<next||owner==null)return;next=Time.time+.1f;
   for(int i=0;i<Buffs.Length;i++){GameObject effect;bool known=active.TryGetValue(Buffs[i],out effect);bool present=!owner.IsDead()&&owner.Buffs.HasBuff(Buffs[i]);
    if(present&&!known){effect=ForestEffects.Spawn(Effects[i],owner.position+Vector3.up,owner.transform,i<2);if(effect!=null)active.Add(Buffs[i],effect);}
    else if(!present&&known){if(effect!=null)Destroy(effect);active.Remove(Buffs[i]);if(!owner.IsDead()&&i<2)ForestEffects.Spawn(i==0?"fxWardExpire":"fxHexExpire",owner.position+Vector3.up,owner.transform);}
   }
  }
  void OnDestroy(){foreach(var pair in active)if(pair.Value!=null)Destroy(pair.Value);active.Clear();}
 }
}
