using System;
using System.Collections.Generic;
using System.IO;
using HarmonyLib;
using UnityEngine;
namespace DelvePresentation {
 [HarmonyPatch(typeof(BlockShapeModelEntity),"PoolCreateCallBack")]
 public static class DelveBlockTargeting {
  static void Postfix(GameObject __0){Apply(__0);}
  public static void Apply(GameObject root){
   if(root==null||!(root.name.StartsWith("delve",StringComparison.Ordinal)||root.name.StartsWith("plantedDelve",StringComparison.Ordinal)))return;
   // Tags in an AssetBundle are serialized as project-local indices. Resolve
   // the game's tag by name after loading instead of trusting an editor index.
   root.layer=16;root.tag="T_Block";
   foreach(var collider in root.GetComponentsInChildren<Collider>(true)){collider.gameObject.layer=16;collider.gameObject.tag="T_Block";collider.isTrigger=false;}
  }
 }
 [HarmonyPatch(typeof(BlockShapeModelEntity),"PoolCreateOnceToAllCallBack")]
 public static class DelveBlockTargetingFirst {static void Postfix(GameObject __0){DelveBlockTargeting.Apply(__0);}}
 public class ModApi:IModApi {
  public static string DirectoryPath;
  static readonly Dictionary<string,GameObject> Prefabs=new Dictionary<string,GameObject>();
  public void InitMod(Mod mod){DirectoryPath=mod.Path;new Harmony("delve.forest.presentation").PatchAll(typeof(ModApi).Assembly);Log.Out("[ForestArt] Native-pose presentation candidate initialized.");}
  public static GameObject Prefab(string bundle,string asset){
   string key=bundle+"?"+asset;GameObject value;if(Prefabs.TryGetValue(key,out value))return value;
   value=DataLoader.LoadAsset<GameObject>("#@modfolder(ZDelvePresentation):Resources/"+bundle+".unity3d?"+asset,true);
   if(value==null)throw new InvalidDataException("Missing presentation asset "+key);Prefabs.Add(key,value);return value;
  }
  public static void Attach(EntityAlive entity){
   if(entity==null||SystemInfo.graphicsDeviceType==UnityEngine.Rendering.GraphicsDeviceType.Null)return;
   if(entity.GetComponent<BuffVisuals>()==null)entity.gameObject.AddComponent<BuffVisuals>();
   string id=EntityClass.GetEntityClassName(entity.entityClass);if(!EnemyRigs.Bundles.ContainsKey(id))return;
   var visual=entity.GetComponent<EnemyVisual>();if(visual==null)visual=entity.gameObject.AddComponent<EnemyVisual>();visual.Bind(entity,id);
  }
 }
 [HarmonyPatch(typeof(EntityAlive),"OnAddedToWorld")]
 public static class SpawnArt {static void Postfix(EntityAlive __instance){ModApi.Attach(__instance);}}
 [HarmonyPatch(typeof(EntityAlive),"OnAvatarRebuilt")]
 public static class RebuildArt {static void Postfix(EntityAlive __instance){ModApi.Attach(__instance);}}
 // The native skeleton remains the authority for attacks, hitboxes and ragdolls.
 // Offsets are calculated from the exported reference bind pose, never the pose
 // an enemy happened to be playing when its visual loaded on a remote client.
 public class EnemyVisual:MonoBehaviour {
  public GameObject Visual {get;private set;}
  public int BonePairs {get{return pairs.Count;}}
  sealed class Pair {public Transform Native,Art;public Matrix4x4 Offset;}
  readonly List<Pair> pairs=new List<Pair>();
  EntityAlive entity;Transform nativeRoot;Renderer[] originals,renderers;Animator[] nativeAnimators;AnimatorCullingMode[] nativeCulling;string id;bool failed;
  public void Bind(EntityAlive owner,string name){entity=owner;id=name;if(nativeRoot!=null&&owner.emodel!=null&&nativeRoot!=owner.emodel.modelTransform)Clear();}
  void Clear(){if(originals!=null)foreach(var r in originals)if(r!=null)r.forceRenderingOff=false;if(nativeAnimators!=null)for(int i=0;i<nativeAnimators.Length;i++)if(nativeAnimators[i]!=null)nativeAnimators[i].cullingMode=nativeCulling[i];nativeAnimators=null;if(Visual!=null)Destroy(Visual);Visual=null;nativeRoot=null;originals=null;pairs.Clear();}
  void Setup(){
   if(entity.emodel==null||entity.emodel.modelTransform==null)return;
   nativeRoot=entity.emodel.modelTransform;originals=nativeRoot.GetComponentsInChildren<Renderer>(true);nativeAnimators=nativeRoot.GetComponentsInChildren<Animator>(true);nativeCulling=new AnimatorCullingMode[nativeAnimators.Length];for(int i=0;i<nativeAnimators.Length;i++){nativeCulling[i]=nativeAnimators[i].cullingMode;nativeAnimators[i].cullingMode=AnimatorCullingMode.AlwaysAnimate;}
   var native=new Dictionary<string,Transform>();foreach(var t in nativeRoot.GetComponentsInChildren<Transform>(true))if(!native.ContainsKey(t.name))native.Add(t.name,t);
   Visual=Instantiate(ModApi.Prefab(EnemyRigs.Bundles[id],id),nativeRoot,false);Visual.name="DelveVisual_"+id;
   Visual.transform.localPosition=Vector3.zero;Visual.transform.localRotation=Quaternion.identity;Visual.transform.localScale=Vector3.one;
   foreach(var animator in Visual.GetComponentsInChildren<Animator>(true)){animator.applyRootMotion=false;animator.enabled=false;}
   var bind=EnemyRigs.Build(id);var artBones=new HashSet<Transform>();renderers=Visual.GetComponentsInChildren<Renderer>(true);
   foreach(var skin in Visual.GetComponentsInChildren<SkinnedMeshRenderer>(true))foreach(var bone in skin.bones)if(bone!=null)artBones.Add(bone);
   foreach(var art in Visual.GetComponentsInChildren<Transform>(true)){
    art.gameObject.layer=originals.Length>0?originals[0].gameObject.layer:gameObject.layer;
    Transform source;Matrix4x4 rest;
    if(native.TryGetValue(art.name,out source)&&bind.TryGetValue(art.name,out rest))pairs.Add(new Pair{Native=source,Art=art,Offset=rest.inverse*Visual.transform.worldToLocalMatrix*art.localToWorldMatrix});
    else if(artBones.Contains(art)&&art.name!="Tail"&&!art.name.StartsWith("Tail",StringComparison.Ordinal))throw new InvalidDataException(id+" unmatched skin bone "+art.name);
   }
   if(pairs.Count<25)throw new InvalidDataException(id+" incomplete native skeleton correspondence");
   foreach(var r in originals)if(r!=null)r.forceRenderingOff=true;
   Log.Out("[ForestArt] Attached "+id+" entity="+entity.entityId+" native bone pairs="+pairs.Count);
  }
  void LateUpdate(){
   if(failed||entity==null)return;
   try{
    if(Visual==null){Setup();if(Visual==null)return;}
    if(entity.emodel==null||entity.emodel.modelTransform!=nativeRoot){Clear();return;}
    for(int i=0;i<nativeAnimators.Length;i++)if(nativeAnimators[i]!=null)nativeAnimators[i].cullingMode=entity.emodel.visible?AnimatorCullingMode.AlwaysAnimate:nativeCulling[i];
    foreach(var pair in pairs){if(pair.Native==null||pair.Art==null)continue;var pose=pair.Native.localToWorldMatrix*pair.Offset;pair.Art.SetPositionAndRotation(pose.GetColumn(3),pose.rotation);pair.Art.gameObject.SetActive(pair.Native.gameObject.activeInHierarchy);}
    foreach(var r in renderers)if(r!=null)r.forceRenderingOff=!entity.emodel.visible;
   }catch(Exception ex){failed=true;Clear();Log.Error("[ForestArt] Native visual fallback for "+id+": "+ex);}
  }
  void OnDestroy(){Log.Out("[ForestArt] Visual owner destroyed: "+id+" entity="+(entity==null?-1:entity.entityId));Clear();}
 }
}

