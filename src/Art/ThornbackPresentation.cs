using System;
using System.Collections.Generic;
using System.IO;
using HarmonyLib;
using UnityEngine;

namespace DelveThornback {
 public class ModApi : IModApi {
  public static string DirectoryPath;
  public static GameObject Prefab;
  public void InitMod(Mod m) {
   DirectoryPath=m.Path;
   new Harmony("delve.thornback.presentation").PatchAll(typeof(ModApi).Assembly);
   Log.Out("[Thornback] Original art bridge initialized; native AI, attack damage and physics retained.");
  }
  public static GameObject GetPrefab() {
   if(Prefab==null)Prefab=DataLoader.LoadAsset<GameObject>("#"+Path.Combine(DirectoryPath,"Resources/thornback.unity3d").Replace('\\','/')+"?delveThornbackBoar",true);
   if(Prefab==null)throw new Exception("Thornback bundle prefab unavailable");
   return Prefab;
  }
  public static void Attach(EntityAlive entity) {
   if(entity==null || EntityClass.GetEntityClassName(entity.entityClass)!="delveThornbackBoar")return;
   if(SystemInfo.graphicsDeviceType==UnityEngine.Rendering.GraphicsDeviceType.Null)return;
   if(entity.GetComponent<ThornbackVisual>()==null)entity.gameObject.AddComponent<ThornbackVisual>();
  }
 }
 [HarmonyPatch(typeof(EntityAlive),"OnAddedToWorld")]
 public static class SpawnArt {static void Postfix(EntityAlive __instance){ModApi.Attach(__instance);}}
 [HarmonyPatch(typeof(EntityAlive),"OnAvatarRebuilt")]
 public static class RebuildArt {static void Postfix(EntityAlive __instance){ModApi.Attach(__instance);}}

 public class ThornbackVisual : MonoBehaviour {
  public GameObject Visual {get;private set;}
  public Animator Animator {get;private set;}
  public string State {get;private set;}
  public bool Ready {get{return Visual!=null && Animator!=null;}}
  public bool ProbeMode;
  public bool ForceVisibleForProbe;
  EntityAlive entity; Renderer[] originals; Renderer[] renderers;
  Transform nativeRoot; readonly List<Transform> nativeBones=new List<Transform>();
  readonly List<Transform> artBones=new List<Transform>(); readonly List<Quaternion> offsets=new List<Quaternion>();
  Vector3 previousPosition; float previousYaw,lockUntil,stationaryTime; bool wasAttack,wasHit,wasSleep,wasTarget,wasRush,failed;
  float deathTime=-1;
  void Start(){entity=GetComponent<EntityAlive>();previousPosition=entity.position;previousYaw=entity.rotation.y;}
  void Setup() {
   if(entity.emodel==null || entity.emodel.modelTransform==null)return;
   nativeRoot=entity.emodel.modelTransform;
   originals=nativeRoot.GetComponentsInChildren<Renderer>(true);
   var lookup=new Dictionary<string,Transform>();
   foreach(var t in nativeRoot.GetComponentsInChildren<Transform>(true))if(!lookup.ContainsKey(t.name))lookup.Add(t.name,t);
   Visual=UnityEngine.Object.Instantiate(ModApi.GetPrefab(),nativeRoot,false);
   Visual.name="Thornback_CustomVisual";
   Visual.transform.localPosition=Vector3.zero;Visual.transform.localRotation=Quaternion.identity;Visual.transform.localScale=Vector3.one;
   Animator=Visual.GetComponent<Animator>();Animator.applyRootMotion=false;Animator.cullingMode=AnimatorCullingMode.AlwaysAnimate;
   renderers=Visual.GetComponentsInChildren<Renderer>(true);
   int layer=originals.Length>0?originals[0].gameObject.layer:gameObject.layer;
   foreach(var t in Visual.GetComponentsInChildren<Transform>(true)) {
    t.gameObject.layer=layer;Transform source;
    if(lookup.TryGetValue(t.name,out source)) {nativeBones.Add(source);artBones.Add(t);offsets.Add(Quaternion.Inverse(source.rotation)*t.rotation);}
   }
   foreach(var r in renderers) {
    r.SetPropertyBlock(null);
   }
   if(nativeBones.Count<30)throw new Exception("Native/custom rig correspondence incomplete: "+nativeBones.Count);
   foreach(var r in originals)if(r!=null)r.forceRenderingOff=true;
   foreach(var r in renderers)if(r!=null)r.forceRenderingOff=!ProbeMode && !ForceVisibleForProbe && !entity.emodel.visible;
   Play("Idle",0,0);
   Log.Out("[Thornback] Attached entity="+entity.entityId+" bonePairs="+nativeBones.Count+" skins="+renderers.Length);
  }
  public void Play(string state,float blend,float hold) {
   if(!Ready)return;
   if(State!=state){Animator.speed=1;Animator.CrossFadeInFixedTime(state,blend,0,0);State=state;}
   lockUntil=Time.time+hold;
  }
  void Update() {
   if(failed || entity==null)return;
   try {
    if(!Ready){Setup();return;}
    if(ProbeMode)return;
    var avatar=entity.emodel.avatarController;
    float speed=(entity.position-previousPosition).magnitude/Mathf.Max(Time.deltaTime,.001f);
    float turn=Mathf.DeltaAngle(previousYaw,entity.rotation.y)/Mathf.Max(Time.deltaTime,.001f);
    previousPosition=entity.position;previousYaw=entity.rotation.y;
    if(entity.IsDead()) {
     if(deathTime<0){deathTime=Time.time;Play("Death",.08f,.8f);}
     else if(Time.time-deathTime>.8f && !entity.emodel.IsRagdollActive)Play("Corpse",.08f,0);
     return;
    }
    bool attack=avatar!=null && avatar.IsAnimationAttackPlaying();
    bool hit=avatar!=null && avatar.IsAnimationHitRunning();
    bool sleeping=entity.IsSleeping;
    bool target=entity.GetAttackTarget()!=null;
    bool rush=entity.Buffs.HasBuff("delveForestRush");
    if(hit && !wasHit)Play("Hit",.035f,.566667f);
    else if(attack && !wasAttack)Play(speed>.7f?"AttackRunning":"Attack",.025f,speed>.7f?.533333f:.4f);
    else if(wasSleep && !sleeping)Play("Wake",.05f,1.333333f);
    else if(wasRush && !rush)Play("Brake",.06f,.45f);
    else if(!wasTarget && target)Play("Alert",.08f,.8f);
    wasAttack=attack;wasHit=hit;wasSleep=sleeping;wasTarget=target;wasRush=rush;
    if(Time.time<lockUntil)return;
    if(sleeping)Play("Sleep",.15f,0);
    else if(entity.Buffs.HasBuff("delveForestBrace"))Play("Brace",.12f,0);
    else if(entity.Buffs.HasBuff("delveForestSpent"))Play("Recovery",.14f,0);
    else if(rush)Play("Rush",.08f,0);
    else if(speed>.15f) {
     string state=speed>1.2f?"Run":"Walk";Play(state,.12f,0);Animator.speed=Mathf.Clamp(speed/(state=="Run"?2.4f:.8f),.5f,1.8f);stationaryTime=0;
    }
    else if(Mathf.Abs(turn)>25)Play(turn<0?"TurnLeft":"TurnRight",.12f,0);
    else {stationaryTime+=Time.deltaTime;if(stationaryTime>14 && !target){Play("Scrape",.12f,1.8f);stationaryTime=0;}else Play("Idle",.18f,0);}
   }catch(Exception e){failed=true;Restore();Log.Error("[Thornback] Art fallback to native: "+e);}
  }
  void LateUpdate() {
   if(!Ready || failed)return;
   foreach(var r in originals)if(r!=null)r.forceRenderingOff=true;
   foreach(var r in renderers)if(r!=null)r.forceRenderingOff=!ProbeMode && !ForceVisibleForProbe && !entity.emodel.visible;
   // Keep native ragdoll/hit bodies authoritative. Copy their final pose to
   // the art rig; there is no second rigidbody simulation or damage callback.
   if(entity.emodel.IsRagdollActive && !ProbeMode) {
    Animator.enabled=false;
    for(int i=0;i<nativeBones.Count;i++)if(nativeBones[i]!=null && artBones[i]!=null){artBones[i].position=nativeBones[i].position;artBones[i].rotation=nativeBones[i].rotation*offsets[i];}
   } else Animator.enabled=true;
   // Native dismemberment hides bones by scale. Mirror that hide state instead
   // of leaving a cosmetic head/limb visible over a removed native body part.
   if(!ProbeMode)for(int i=0;i<nativeBones.Count;i++)if(nativeBones[i]!=null && artBones[i]!=null && nativeBones[i].localScale.sqrMagnitude<.01f)artBones[i].localScale=Vector3.zero;
  }
  void Restore() {
   if(originals!=null)foreach(var r in originals)if(r!=null)r.forceRenderingOff=false;
   if(Visual!=null)UnityEngine.Object.Destroy(Visual);
  }
  void OnDestroy(){Restore();}
 }
}
