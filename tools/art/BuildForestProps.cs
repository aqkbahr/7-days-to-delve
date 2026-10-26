using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

public static class BuildForestProps {
 [Serializable] public class AssetSpec {public string id;public string family;public string slot;public string kind;public float[] footprint;public int clips;public string[] loops;}
 [Serializable] public class Alias {public string id,target;}
 [Serializable] public class Input {public AssetSpec[] assets;public Alias[] aliases;}
 static string Short(string n){return n.Contains("|")?n.Substring(n.LastIndexOf('|')+1):n;}
 static void Anchor(GameObject owner,string name,Vector3 position){var o=new GameObject(name);o.transform.SetParent(owner.transform,false);o.transform.localPosition=position;}
 public static void Run(){try{ var tags=new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset")[0]);var list=tags.FindProperty("tags");bool found=false;for(int i=0;i<list.arraySize;i++)if(list.GetArrayElementAtIndex(i).stringValue=="T_Block")found=true;if(!found){list.InsertArrayElementAtIndex(list.arraySize);list.GetArrayElementAtIndex(list.arraySize-1).stringValue="T_Block";tags.ApplyModifiedProperties();}
  AssetDatabase.Refresh();var input=JsonUtility.FromJson<Input>(File.ReadAllText("Assets/build-input.json"));
  Directory.CreateDirectory("Assets/Generated");Directory.CreateDirectory("../Bundle");
  var report=new System.Text.StringBuilder();var paths=new List<string>();var addresses=new List<string>();
  var ti=(TextureImporter)AssetImporter.GetAtPath("Assets/ForestPropAtlas.png");ti.maxTextureSize=2048;ti.textureCompression=TextureImporterCompression.CompressedHQ;ti.SaveAndReimport();
  AssetDatabase.DeleteAsset("Assets/Generated/ForestProp.mat");var material=new Material(Shader.Find("Standard"));material.name="ForestPropSurface";material.mainTexture=AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/ForestPropAtlas.png");material.SetFloat("_Glossiness",.22f);AssetDatabase.CreateAsset(material,"Assets/Generated/ForestProp.mat");
  var botanicalIds=new HashSet<string>();Material botanical=null;
  if(File.Exists("Assets/botanical-models.json")){
   foreach(var spec in JsonUtility.FromJson<Input>(File.ReadAllText("Assets/botanical-models.json")).assets)botanicalIds.Add(spec.id);
   foreach(string channel in new[]{"Albedo","Normal"}){var bi=(TextureImporter)AssetImporter.GetAtPath("Assets/BotanicalTextures/"+channel+".png");bi.sRGBTexture=channel=="Albedo";bi.maxTextureSize=2048;bi.npotScale=TextureImporterNPOTScale.None;bi.textureCompression=TextureImporterCompression.CompressedHQ;if(channel=="Normal")bi.textureType=TextureImporterType.NormalMap;bi.SaveAndReimport();}
   string bp="Assets/BotanicalSurface.mat";botanical=AssetDatabase.LoadAssetAtPath<Material>(bp);if(botanical==null){botanical=new Material(Shader.Find("Delve/BotanicalSurface"));AssetDatabase.CreateAsset(botanical,bp);}botanical.mainTexture=AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/BotanicalTextures/Albedo.png");botanical.SetTexture("_BumpMap",AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/BotanicalTextures/Normal.png"));botanical.SetFloat("_BumpScale",.32f);EditorUtility.SetDirty(botanical);
  }
  foreach(var spec in input.assets){
   var selectedMaterial=botanicalIds.Contains(spec.id)?botanical:material;
   string path="Assets/Models/"+spec.id+".fbx";var importer=(ModelImporter)AssetImporter.GetAtPath(path);importer.animationType=ModelImporterAnimationType.Generic;importer.isReadable=true;importer.importCameras=false;importer.importLights=false;importer.optimizeGameObjects=false;importer.animationCompression=ModelImporterAnimationCompression.Off;importer.SaveAndReimport();
   var clips=importer.defaultClipAnimations;foreach(var c in clips){c.name=Short(c.name);c.loopTime=spec.loops.Contains(c.name);c.lockRootPositionXZ=true;c.lockRootHeightY=true;c.lockRootRotation=true;}importer.clipAnimations=clips;importer.SaveAndReimport();
   string cp="Assets/Generated/"+spec.id+".controller";AssetDatabase.DeleteAsset(cp);var controller=AnimatorController.CreateAnimatorControllerAtPath(cp);
   var animations=AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().Where(c=>!c.name.StartsWith("__preview__")).ToArray();
   if(animations.Length!=spec.clips)throw new Exception(spec.id+" clip count "+animations.Length+" expected "+spec.clips);
   foreach(var clip in animations){if(clip.events.Length!=0)throw new Exception("Unexpected animation event");var state=controller.layers[0].stateMachine.AddState(Short(clip.name));state.motion=clip;state.writeDefaultValues=true;if(Short(clip.name)=="Idle"&&!(botanicalIds.Contains(spec.id)&&spec.kind=="plant")||Short(clip.name)=="Sway"&&botanicalIds.Contains(spec.id)&&spec.kind=="plant")controller.layers[0].stateMachine.defaultState=state;}
   var instance=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(path));instance.name=spec.id;var animator=instance.GetComponent<Animator>();if(animator==null)animator=instance.AddComponent<Animator>();animator.runtimeAnimatorController=controller;animator.applyRootMotion=false;animator.cullingMode=AnimatorCullingMode.AlwaysAnimate;
   var skins=instance.GetComponentsInChildren<SkinnedMeshRenderer>(true);if(skins.Length!=3)throw new Exception(spec.id+" skins="+skins.Length);var lods=new LOD[3];
   for(int i=0;i<3;i++){var skin=skins.Single(s=>s.name==spec.slot+"_LOD"+i);skin.sharedMaterials=new[]{selectedMaterial};skin.updateWhenOffscreen=true;skin.gameObject.SetActive(true);skin.enabled=true;skin.localBounds=new Bounds(new Vector3(0,1,0),Vector3.one*4);lods[i]=new LOD(new[]{.40f,.16f,.02f}[i],new Renderer[]{skin});}
   var lod=instance.GetComponent<LODGroup>();if(lod==null)lod=instance.AddComponent<LODGroup>();lod.SetLODs(lods);lod.RecalculateBounds();
   if(spec.kind=="station" || spec.kind=="plant"){
    var fit=new Mesh();var fitSkin=skins.Single(s=>s.name=="Prop_LOD0");fitSkin.BakeMesh(fit);var vtx=fit.vertices;var bounds=new Bounds(instance.transform.InverseTransformPoint(fitSkin.transform.TransformPoint(vtx[0])),Vector3.zero);foreach(var v in vtx)bounds.Encapsulate(instance.transform.InverseTransformPoint(fitSkin.transform.TransformPoint(v)));
    if(spec.kind=="station" && (bounds.size.x>spec.footprint[0]+.02f || bounds.size.y>spec.footprint[1]+.02f || bounds.size.z>spec.footprint[2]+.02f || bounds.min.y<-.03f))throw new Exception("Station footprint exceeded "+spec.id+" "+bounds);
    instance.layer=16;instance.tag="T_Block";var interaction=instance.AddComponent<BoxCollider>();interaction.center=bounds.center;interaction.size=bounds.size+Vector3.one*.005f;interaction.isTrigger=false;Anchor(instance,spec.kind=="plant"?"HarvestSocket":"InteractionSocket",spec.kind=="plant"?bounds.center:new Vector3(0,Mathf.Min(.8f,bounds.center.y),bounds.max.z+.025f));UnityEngine.Object.DestroyImmediate(fit);
    if(spec.family=="hearth")Anchor(instance,"EmberSocket",new Vector3(0,.32f,0));
    if(spec.family=="forge"){Anchor(instance,"EmberSocket",new Vector3(.35f,.65f,.06f));Anchor(instance,"SmokeSocket",new Vector3(.35f,1.79f,-.24f));}
    if(spec.family=="collector"){Anchor(instance,"SpoutSocket",new Vector3(0,1.05f,0));for(int j=0;j<9;j++)Anchor(instance,"JarSlot"+(j+1),new Vector3(.72f-j*.18f,.36f,.87f));}
   }
   string pp="Assets/Generated/"+spec.id+".prefab";PrefabUtility.SaveAsPrefabAsset(instance,pp);paths.Add(pp);addresses.Add(spec.id);
   // Static inventory/drop representation with bounded pickup collider.
   var skin0=skins.Single(s=>s.name==spec.slot+"_LOD0");var dropMesh=new Mesh();skin0.BakeMesh(dropMesh);var vertices=dropMesh.vertices;for(int v=0;v<vertices.Length;v++)vertices[v]=instance.transform.InverseTransformPoint(skin0.transform.TransformPoint(vertices[v]));dropMesh.vertices=vertices;dropMesh.RecalculateNormals();dropMesh.RecalculateBounds();var center=dropMesh.bounds.center;for(int v=0;v<vertices.Length;v++)vertices[v]-=center;dropMesh.vertices=vertices;dropMesh.RecalculateBounds();
   string meshPath="Assets/Generated/"+spec.id+"_Drop.asset";AssetDatabase.DeleteAsset(meshPath);AssetDatabase.CreateAsset(dropMesh,meshPath);var drop=new GameObject(spec.id+"_Drop");drop.AddComponent<MeshFilter>().sharedMesh=dropMesh;drop.AddComponent<MeshRenderer>().sharedMaterial=selectedMaterial;var collider=drop.AddComponent<BoxCollider>();collider.center=dropMesh.bounds.center;collider.size=dropMesh.bounds.size+Vector3.one*.005f;
   string dp="Assets/Generated/"+spec.id+"_Drop.prefab";PrefabUtility.SaveAsPrefabAsset(drop,dp);paths.Add(dp);addresses.Add(spec.id+"_Drop");UnityEngine.Object.DestroyImmediate(drop);
   report.AppendLine(spec.id+" clips="+animations.Length+" triangles="+String.Join("/",skins.Select(s=>(s.sharedMesh.triangles.Length/3).ToString()).ToArray()));UnityEngine.Object.DestroyImmediate(instance);
  }
  foreach(var alias in input.aliases){var instance=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Generated/"+alias.target+".prefab"));instance.name=alias.id;string path="Assets/Generated/"+alias.id+".prefab";PrefabUtility.SaveAsPrefabAsset(instance,path);paths.Add(path);addresses.Add(alias.id);UnityEngine.Object.DestroyImmediate(instance);report.AppendLine(alias.id+" shares art with "+alias.target);}
  // Original bounded visual effects, with no damage, heat or collector callbacks.
  var sprite=new Texture2D(64,64,TextureFormat.RGBA32,false);var pixels=new Color[4096];for(int y=0;y<64;y++)for(int x=0;x<64;x++){float d=new Vector2((x-31.5f)/31.5f,(y-31.5f)/31.5f).magnitude;pixels[y*64+x]=new Color(1,1,1,Mathf.Pow(Mathf.Clamp01(1-d),2));}sprite.SetPixels(pixels);sprite.Apply();File.WriteAllBytes("Assets/Generated/StationParticle.png",sprite.EncodeToPNG());UnityEngine.Object.DestroyImmediate(sprite);AssetDatabase.Refresh();
  string mp="Assets/Generated/StationParticle.mat";AssetDatabase.DeleteAsset(mp);var fxmat=new Material(Shader.Find("Legacy Shaders/Particles/Alpha Blended"));fxmat.mainTexture=AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Generated/StationParticle.png");fxmat.SetColor("_TintColor",Color.white);AssetDatabase.CreateAsset(fxmat,mp);
  foreach(string id in new[]{"fxHearthEmbers","fxForgeSmoke","fxCollectorDrip"}){
   var go=new GameObject(id);var ps=go.AddComponent<ParticleSystem>();ps.Stop(true,ParticleSystemStopBehavior.StopEmittingAndClear);var main=ps.main;main.loop=false;main.duration=2;main.startLifetime=id=="fxForgeSmoke"?1.5f:.65f;main.startSpeed=id=="fxCollectorDrip"?.6f:.25f;main.startSize=id=="fxForgeSmoke"?.20f:.035f;main.startColor=id=="fxHearthEmbers"?new Color(1,.38f,.05f,.8f):id=="fxForgeSmoke"?new Color(.3f,.29f,.27f,.3f):new Color(.4f,.7f,.9f,.7f);main.maxParticles=64;main.playOnAwake=true;main.stopAction=ParticleSystemStopAction.Destroy;
   var em=ps.emission;em.rateOverTime=12;var shape=ps.shape;shape.shapeType=ParticleSystemShapeType.Cone;shape.angle=8;shape.radius=id=="fxCollectorDrip"?.015f:.12f;shape.rotation=new Vector3(id=="fxCollectorDrip"?90:-90,0,0);var col=ps.colorOverLifetime;col.enabled=true;var gradient=new Gradient();gradient.SetKeys(new[]{new GradientColorKey(Color.white,0),new GradientColorKey(Color.white,1)},new[]{new GradientAlphaKey(0,0),new GradientAlphaKey(1,.15f),new GradientAlphaKey(0,1)});col.color=gradient;ps.GetComponent<ParticleSystemRenderer>().sharedMaterial=fxmat;
   string path="Assets/Generated/"+id+".prefab";PrefabUtility.SaveAsPrefabAsset(go,path);paths.Add(path);addresses.Add(id);UnityEngine.Object.DestroyImmediate(go);report.AppendLine(id+" cappedParticles=64 expires=true no gameplay callbacks");
  }
  AssetDatabase.SaveAssets();
  var bundle=new AssetBundleBuild{assetBundleName="forestprops.unity3d",assetNames=paths.ToArray(),addressableNames=addresses.ToArray()};if(BuildPipeline.BuildAssetBundles("../Bundle",new[]{bundle},BuildAssetBundleOptions.ChunkBasedCompression|BuildAssetBundleOptions.ForceRebuildAssetBundle,BuildTarget.StandaloneWindows64)==null)throw new Exception("Bundle build failed");
  File.WriteAllText("../unity-build-result.txt","PASS\n"+report);EditorApplication.Exit(0);
 }catch(Exception e){Debug.LogException(e);File.WriteAllText("../unity-build-result.txt","FAIL\n"+e);EditorApplication.Exit(1);}}
}



