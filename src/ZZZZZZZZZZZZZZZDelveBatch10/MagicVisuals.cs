using System;using System.Collections.Generic;using HarmonyLib;using UnityEngine;using DelvePresentation;
namespace DelveBatchTen {
 public static class Magic {
  public static string Family(ItemValue v){if(v==null||v.ItemClass==null)return null;string n=v.ItemClass.GetItemName();if(!n.StartsWith("delve"))return null;if(n.Contains("Wand"))return "wand";if(n.Contains("Staff"))return "staff";if(n.Contains("MendingTotem"))return "heal";if(n.Contains("WardTotem"))return "ward";if(n=="delveStarterTotem"||n=="delveForgedTotem")return "hex";return null;}
  public static Color ColorFor(string f){return f=="wand"?new Color(.30f,.65f,1):f=="staff"?new Color(1,.32f,.055f):f=="heal"?new Color(.22f,.90f,.48f):f=="hex"?new Color(.65f,.22f,.90f):new Color(.30f,.80f,.95f);}
  public static bool Reloading(ItemActionRanged.ItemActionDataRanged d){return d!=null&&!d.isReloadCancelled&&!d.isWeaponReloadCancelled&&(d.isReloading||d.isWeaponReloading||d.isReloadRequested);}
  public static Material Material(Color color){var shader=Shader.Find("Unlit/Color")??Shader.Find("Standard");var m=new Material(shader);m.color=color;if(m.HasProperty("_EmissionColor")){m.EnableKeyword("_EMISSION");m.SetColor("_EmissionColor",color*3);}return m;}
  public static MagicHold Held(ItemActionData d){return d==null||d.invData.model==null?null:d.invData.model.GetComponent<MagicHold>();}
 }
 [HarmonyPatch(typeof(ItemInventoryData),"BuildModel")] public static class HeldBuild {
  [HarmonyPriority(Priority.Last)] static void Postfix(ItemInventoryData __instance){if(SystemInfo.graphicsDeviceType==UnityEngine.Rendering.GraphicsDeviceType.Null||__instance.model==null)return;if(Magic.Family(__instance.itemValue)!=null){var m=__instance.model.GetComponent<MagicHold>()??__instance.model.gameObject.AddComponent<MagicHold>();m.Bind(__instance);}else if(Scythe.Is(__instance.itemValue)&&__instance.model.Find("DelveScythe")==null){var original=__instance.model.GetComponentsInChildren<Renderer>(true);var prefab=DataLoader.LoadAsset<GameObject>("#@modfolder(DelveBatch10):Resources/batchten.unity3d?delveHarvestScythe",true);var model=UnityEngine.Object.Instantiate(prefab,__instance.model,false);model.name="DelveScythe";foreach(var r in original)r.forceRenderingOff=true;foreach(var t in model.GetComponentsInChildren<Transform>(true))t.gameObject.layer=__instance.model.gameObject.layer;}}
 }
 // Leave native reload events and ammunition timing running, but hold the
 // previously displayed arm/grip pose instead of displaying firearm motions.
 [DefaultExecutionOrder(32000)] public class MagicHold:MonoBehaviour {
  public bool Pending;ItemInventoryData data;GameObject glow;Material material;readonly Dictionary<Transform,Pose> poses=new Dictionary<Transform,Pose>();
  struct Pose {public Vector3 Position;public Quaternion Rotation;}
  public void Bind(ItemInventoryData d){data=d;var roots=new[]{d.holdingEntity.RootTransform,transform.root,d.holdingEntity.emodel==null?null:d.holdingEntity.emodel.GetModelTransform()};foreach(var root in roots)if(root!=null)foreach(var t in root.GetComponentsInChildren<Transform>(true)){string n=t.name.ToLowerInvariant();if(n.Contains("arm")||n.Contains("hand")||n.Contains("finger")||n.Contains("thumb"))poses[t]=new Pose{Position=t.localPosition,Rotation=t.localRotation};}poses[transform]=new Pose{Position=transform.localPosition,Rotation=transform.localRotation};}
  void LateUpdate(){if(data==null)return;bool active=Pending;foreach(var a in data.actionData)active|=Magic.Reloading(a as ItemActionRanged.ItemActionDataRanged);
   var keys=new List<Transform>(poses.Keys);foreach(var t in keys){if(t==null)continue;if(active){var p=poses[t];t.localPosition=p.Position;t.localRotation=p.Rotation;}else poses[t]=new Pose{Position=t.localPosition,Rotation=t.localRotation};}
   if(glow==null){var held=GetComponent<HeldVisual>();if(held==null||held.EffectOrigin==null)return;glow=GameObject.CreatePrimitive(PrimitiveType.Sphere);glow.name="DelveGemRecharge";Destroy(glow.GetComponent<Collider>());glow.transform.SetParent(held.EffectOrigin,false);glow.transform.localScale=Vector3.one*.09f;glow.layer=gameObject.layer;material=Magic.Material(Magic.ColorFor(Magic.Family(data.itemValue)));glow.GetComponent<Renderer>().sharedMaterial=material;var light=glow.AddComponent<Light>();light.color=material.color;light.range=.65f;light.intensity=1.2f;}
   glow.SetActive(active);
  }
  void OnDestroy(){if(glow!=null)Destroy(glow);if(material!=null)Destroy(material);}
 }
 [HarmonyPatch(typeof(ItemActionRanged),"ReloadGun")] public static class RechargeStart {static void Prefix(ItemActionData __0){var h=Magic.Held(__0);if(h!=null&&!__0.invData.holdingEntity.isEntityRemote)h.Pending=true;}}
 [HarmonyPatch(typeof(ItemActionRanged),"CompleteReload")] public static class RechargeEnd {static void Postfix(ItemActionRanged.ItemActionDataRanged __0){var h=Magic.Held(__0);if(h!=null)h.Pending=false;}}
 [HarmonyPatch(typeof(ItemActionRanged),"CancelReload")] public static class RechargeCancel {static void Postfix(ItemActionData __0){var h=Magic.Held(__0);if(h!=null)h.Pending=false;}}
 [HarmonyPatch(typeof(ItemActionRanged),"StopHolding")] public static class RechargeStop {static void Prefix(ItemActionData __0){var h=Magic.Held(__0);if(h!=null)h.Pending=false;}}
 // Replace the old generic completion burst; the gem now supplies recharge feedback.
 [HarmonyPatch(typeof(ItemActionRanged),"fireShot")] public static class BoltCast {
  static void Postfix(int __0,ItemActionRanged.ItemActionDataRanged __1,Vector3 __result){if(__0!=0||SystemInfo.graphicsDeviceType==UnityEngine.Rendering.GraphicsDeviceType.Null)return;string f=Magic.Family(__1.invData.itemValue);if(f!="wand"&&f!="staff")return;var owner=__1.invData.holdingEntity;var ray=owner.GetLookRay();ray.direction=__result.normalized;float range=EffectManager.GetValue(PassiveEffects.MaxRange,__1.invData.itemValue,40,owner);range=Mathf.Clamp(range,1,80);Vector3 end=ray.origin+ray.direction*range;RaycastHit hit;if(Physics.Raycast(new Ray(ray.origin-Origin.position,ray.direction),out hit,range,Physics.DefaultRaycastLayers,QueryTriggerInteraction.Ignore))end=hit.point+Origin.position;var held=__1.invData.model==null?null:__1.invData.model.GetComponent<HeldVisual>();Vector3 start=held!=null&&held.EffectOrigin!=null?held.EffectOrigin.position+Origin.position:ray.origin+ray.direction*.5f;MagicBolt.Spawn(start,end,Magic.ColorFor(f));}
 }
 public class MagicBolt:MonoBehaviour {
  static int active;Vector3 start,end;float elapsed,duration;Material material;
  public static void Spawn(Vector3 a,Vector3 b,Color color){if(active>=64)return;var g=GameObject.CreatePrimitive(PrimitiveType.Sphere);g.name="DelveVisibleSpellBolt";Destroy(g.GetComponent<Collider>());g.transform.position=a-Origin.position;g.transform.localScale=Vector3.one*.1f;var bolt=g.AddComponent<MagicBolt>();active++;bolt.start=a;bolt.end=b;bolt.duration=Mathf.Clamp(Vector3.Distance(a,b)/25,.10f,3.2f);bolt.material=Magic.Material(color);g.GetComponent<Renderer>().sharedMaterial=bolt.material;var trail=g.AddComponent<TrailRenderer>();trail.sharedMaterial=bolt.material;trail.time=.12f;trail.startWidth=.075f;trail.endWidth=0;Destroy(g,4);}
  void Update(){elapsed+=Time.deltaTime;transform.position=Vector3.Lerp(start,end,elapsed/duration)-Origin.position;if(elapsed>=duration)Destroy(gameObject);}
  void OnDestroy(){active=Math.Max(0,active-1);if(material!=null)Destroy(material);}
 }
}
