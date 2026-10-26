using System;using System.Collections.Generic;using HarmonyLib;using UnityEngine;
namespace DelvePresentation {
 [HarmonyPatch(typeof(ItemInventoryData),"BuildModel")]
 public static class HeldBuild {static void Postfix(ItemInventoryData __instance){
  if(SystemInfo.graphicsDeviceType==UnityEngine.Rendering.GraphicsDeviceType.Null||__instance.model==null||__instance.itemValue==null)return;
  string[] entry;if(!HeldCatalog.Items.TryGetValue(__instance.itemValue.ItemClass.GetItemName(),out entry)||__instance.model.GetComponent<HeldVisual>()!=null)return;
  var visual=__instance.model.gameObject.AddComponent<HeldVisual>();visual.Bind(__instance,entry[0],entry[1]);
 }}
 public class HeldVisual:MonoBehaviour {
  public GameObject Visual {get;private set;} public Transform EffectOrigin {get;private set;}
  ItemInventoryData data;Renderer[] originals;readonly List<Renderer> leftRenderers=new List<Renderer>();Animator animator;Transform nativeString,leftBone,leftWeapon,ammo;Vector3 stringRest;Quaternion leftRest;string family;float nextLeftSearch;bool ready;
  static Transform Find(Transform root,string name){foreach(var t in root.GetComponentsInChildren<Transform>(true))if(t.name==name)return t;return null;}
  public void Bind(ItemInventoryData owner,string asset,string kind){
   data=owner;family=kind;originals=GetComponentsInChildren<Renderer>(true);
   try{
    nativeString=Find(transform,kind=="bow"?"bowString":"String");if(nativeString==null&&kind=="bow")nativeString=Find(transform,"ProjectileJoint");if(nativeString!=null)stringRest=nativeString.localPosition;
    Visual=Instantiate(ModApi.Prefab("forestweapons",asset),transform,false);Visual.name="DelveHeld_"+asset;
    Visual.transform.localPosition=Vector3.zero;Visual.transform.localRotation=(kind=="wand"||kind=="staff"||kind=="hex"||kind=="heal"||kind=="ward")?Quaternion.Euler(90,0,0):Quaternion.identity;
    foreach(var t in Visual.GetComponentsInChildren<Transform>(true))t.gameObject.layer=gameObject.layer;
    foreach(var c in Visual.GetComponentsInChildren<Collider>(true))c.enabled=false;
    animator=Visual.GetComponent<Animator>();if(animator!=null){animator.applyRootMotion=false;animator.enabled=false;}
    if(kind=="spear"){
     // The FBX carries its preview idle pose (-6cm, -8 degrees). Native spear
     // animation already supplies that motion; restore the authored grip first.
     var weapon=Find(Visual.transform,"Weapon");if(weapon!=null){weapon.localPosition=Vector3.zero;weapon.localRotation=Quaternion.identity;}
     var grip=Find(Visual.transform,"GripRight");
     if(grip!=null)Visual.transform.localPosition-=transform.InverseTransformPoint(grip.position);
    }
    if(kind=="staff"||kind=="hex"||kind=="heal"||kind=="ward"){
     var weapon=Find(Visual.transform,"Weapon");if(weapon!=null){weapon.localPosition=Vector3.zero;weapon.localRotation=Quaternion.identity;}
     var grip=Find(Visual.transform,"GripRight");if(grip!=null)Visual.transform.localPosition-=transform.InverseTransformPoint(grip.position);
    }
    if(asset=="delveBoneDagger"){
     // The imported animation preview displaces Weapon from the authored grip.
     // Native boneShiv is 0.427m long; this authored dagger is 0.565m long.
     var weapon=Find(Visual.transform,"Weapon");if(weapon!=null){weapon.localPosition=Vector3.zero;weapon.localRotation=Quaternion.identity;}
     Visual.transform.localScale=Vector3.one*.756f;
     var grip=Find(Visual.transform,"GripRight");
     if(grip!=null)Visual.transform.localPosition-=transform.InverseTransformPoint(grip.position);
     Visual.transform.localPosition+=new Vector3(0,0,-.017f);
    }
    EffectOrigin=Find(Visual.transform,"EffectOriginSocket");ammo=Find(Visual.transform,"Ammo");
    leftBone=Find(Visual.transform,"LeftWrap");if(leftBone!=null)leftRest=Quaternion.Inverse(Visual.transform.rotation)*leftBone.rotation;
    foreach(var r in originals)r.forceRenderingOff=true;ready=true;
   }catch(Exception ex){Log.Error("[ForestArt] Held fallback "+asset+": "+ex);Clear();}
  }
  void LateUpdate(){if(!ready||Visual==null||data==null)return;
   foreach(var r in originals)if(r!=null)r.forceRenderingOff=true;
   if((family=="bow"||family=="crossbow")&&animator!=null&&nativeString!=null){float draw=Mathf.Clamp01(Vector3.Distance(nativeString.localPosition,stringRest)/.35f);animator.Play("Draw",0,draw);animator.Update(0);if(ammo!=null)ammo.gameObject.SetActive(data.itemValue.Meta>0);}
   if(family=="wraps"&&leftBone!=null){
    if(Time.time>=nextLeftSearch){nextLeftSearch=Time.time+.25f;var root=data.holdingEntity.RootTransform;if(leftWeapon==null&&root!=null)leftWeapon=Find(root,"LeftWeapon");if(leftWeapon!=null)foreach(var r in leftWeapon.GetComponentsInChildren<Renderer>(true))if(!r.transform.IsChildOf(Visual.transform)){r.forceRenderingOff=true;if(!leftRenderers.Contains(r))leftRenderers.Add(r);}}
    if(leftWeapon!=null)leftBone.SetPositionAndRotation(leftWeapon.position,leftWeapon.rotation*leftRest);
   }
  }
  void Clear(){ready=false;if(originals!=null)foreach(var r in originals)if(r!=null)r.forceRenderingOff=false;foreach(var r in leftRenderers)if(r!=null)r.forceRenderingOff=false;if(Visual!=null)Destroy(Visual);Visual=null;}
  void OnDestroy(){Clear();}
 }
}
