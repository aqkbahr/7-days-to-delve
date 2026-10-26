using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

public static class BuildForestArmor {
 [Serializable] public class AssetSpec {public string id;public string family;public string slot;public int clips;public string[] loops;}
 [Serializable] public class Input {public AssetSpec[] assets;}
 static string Short(string n){return n.Contains("|")?n.Substring(n.LastIndexOf('|')+1):n;}
 public static void Run(){try{
  AssetDatabase.Refresh();var input=JsonUtility.FromJson<Input>(File.ReadAllText("Assets/build-input.json"));
  Directory.CreateDirectory("Assets/Generated");Directory.CreateDirectory("../Bundle");
  var report=new System.Text.StringBuilder();var paths=new List<string>();var addresses=new List<string>();
  var ti=(TextureImporter)AssetImporter.GetAtPath("Assets/ForestArmorAtlas.png");ti.maxTextureSize=2048;ti.textureCompression=TextureImporterCompression.CompressedHQ;ti.SaveAndReimport();
  AssetDatabase.DeleteAsset("Assets/Generated/ForestArmor.mat");var material=new Material(Shader.Find("Standard"));material.name="ForestArmorSurface";material.mainTexture=AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/ForestArmorAtlas.png");material.SetFloat("_Glossiness",.22f);AssetDatabase.CreateAsset(material,"Assets/Generated/ForestArmor.mat");
  foreach(var spec in input.assets){
   string path="Assets/Models/"+spec.id+".fbx";var importer=(ModelImporter)AssetImporter.GetAtPath(path);importer.animationType=ModelImporterAnimationType.Generic;importer.isReadable=true;importer.importCameras=false;importer.importLights=false;importer.optimizeGameObjects=false;importer.animationCompression=ModelImporterAnimationCompression.Off;importer.SaveAndReimport();
   var clips=importer.defaultClipAnimations;foreach(var c in clips){c.name=Short(c.name);c.loopTime=spec.loops.Contains(c.name);c.lockRootPositionXZ=true;c.lockRootHeightY=true;c.lockRootRotation=true;}importer.clipAnimations=clips;importer.SaveAndReimport();
   string cp="Assets/Generated/"+spec.id+".controller";AssetDatabase.DeleteAsset(cp);var controller=AnimatorController.CreateAnimatorControllerAtPath(cp);
   var animations=AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().Where(c=>!c.name.StartsWith("__preview__")).ToArray();
   if(animations.Length!=spec.clips)throw new Exception(spec.id+" clip count "+animations.Length+" expected "+spec.clips);
   foreach(var clip in animations){if(clip.events.Length!=0)throw new Exception("Unexpected animation event");var state=controller.layers[0].stateMachine.AddState(Short(clip.name));state.motion=clip;state.writeDefaultValues=true;if(Short(clip.name)=="Idle")controller.layers[0].stateMachine.defaultState=state;}
   var instance=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(path));instance.name=spec.id;var animator=instance.GetComponent<Animator>();if(animator==null)animator=instance.AddComponent<Animator>();animator.runtimeAnimatorController=controller;animator.applyRootMotion=false;animator.cullingMode=AnimatorCullingMode.AlwaysAnimate;
   var skins=instance.GetComponentsInChildren<SkinnedMeshRenderer>(true);if(skins.Length!=3)throw new Exception(spec.id+" skins="+skins.Length);var lods=new LOD[3];
   for(int i=0;i<3;i++){var skin=skins.Single(s=>s.name==spec.slot+"_LOD"+i);skin.sharedMaterials=new[]{material};skin.updateWhenOffscreen=true;skin.gameObject.SetActive(true);skin.enabled=true;skin.localBounds=new Bounds(new Vector3(0,1,0),Vector3.one*4);lods[i]=new LOD(new[]{.40f,.16f,.02f}[i],new Renderer[]{skin});}
   var lod=instance.GetComponent<LODGroup>();if(lod==null)lod=instance.AddComponent<LODGroup>();lod.SetLODs(lods);lod.RecalculateBounds();
   string pp="Assets/Generated/"+spec.id+".prefab";PrefabUtility.SaveAsPrefabAsset(instance,pp);paths.Add(pp);addresses.Add(spec.id);
   // Static inventory/drop representation with bounded pickup collider.
   var skin0=skins.Single(s=>s.name==spec.slot+"_LOD0");var dropMesh=new Mesh();skin0.BakeMesh(dropMesh);var vertices=dropMesh.vertices;for(int v=0;v<vertices.Length;v++)vertices[v]=instance.transform.InverseTransformPoint(skin0.transform.TransformPoint(vertices[v]));if(spec.slot=="Gloves")for(int v=0;v<vertices.Length;v++)vertices[v].x-=Mathf.Sign(vertices[v].x)*.42f;dropMesh.vertices=vertices;dropMesh.RecalculateNormals();dropMesh.RecalculateBounds();var center=dropMesh.bounds.center;for(int v=0;v<vertices.Length;v++)vertices[v]-=center;dropMesh.vertices=vertices;dropMesh.RecalculateBounds();
   string meshPath="Assets/Generated/"+spec.id+"_Drop.asset";AssetDatabase.DeleteAsset(meshPath);AssetDatabase.CreateAsset(dropMesh,meshPath);var drop=new GameObject(spec.id+"_Drop");drop.AddComponent<MeshFilter>().sharedMesh=dropMesh;drop.AddComponent<MeshRenderer>().sharedMaterial=material;var collider=drop.AddComponent<BoxCollider>();collider.center=dropMesh.bounds.center;collider.size=dropMesh.bounds.size+Vector3.one*.005f;
   string dp="Assets/Generated/"+spec.id+"_Drop.prefab";PrefabUtility.SaveAsPrefabAsset(drop,dp);paths.Add(dp);addresses.Add(spec.id+"_Drop");UnityEngine.Object.DestroyImmediate(drop);
   // Native SDCS clones this slot subtree and remaps its bones onto the player.
   // Keep the reference skeleton outside the subtree; do not animate a second rig.
   string part=spec.slot=="Helmet"?"head":spec.slot=="Outfit"?"body":spec.slot=="Gloves"?"hands":"feet";
   UnityEngine.Object.DestroyImmediate(animator);UnityEngine.Object.DestroyImmediate(lod);
   var wornPart=new GameObject(part);wornPart.transform.SetParent(instance.transform,false);
   foreach(var skin in skins){
    skin.transform.SetParent(wornPart.transform,true);
    // SDCS only needs weighted bones. FBX includes unused reference bones that
    // differ between player archetypes and otherwise become null after stitching.
    var mesh=UnityEngine.Object.Instantiate(skin.sharedMesh);var weights=mesh.boneWeights;var used=new SortedSet<int>();
    foreach(var w in weights){if(w.weight0>0)used.Add(w.boneIndex0);if(w.weight1>0)used.Add(w.boneIndex1);if(w.weight2>0)used.Add(w.boneIndex2);if(w.weight3>0)used.Add(w.boneIndex3);}
    var indices=used.ToArray();var map=new Dictionary<int,int>();for(int j=0;j<indices.Length;j++)map[indices[j]]=j;
    for(int j=0;j<weights.Length;j++){var w=weights[j];w.boneIndex0=w.weight0>0?map[w.boneIndex0]:0;w.boneIndex1=w.weight1>0?map[w.boneIndex1]:0;w.boneIndex2=w.weight2>0?map[w.boneIndex2]:0;w.boneIndex3=w.weight3>0?map[w.boneIndex3]:0;weights[j]=w;}
    var oldBones=skin.bones;var oldPoses=mesh.bindposes;mesh.boneWeights=weights;mesh.bindposes=indices.Select(j=>oldPoses[j]).ToArray();skin.bones=indices.Select(j=>oldBones[j]).ToArray();
    string pathWornMesh="Assets/Generated/"+spec.id+"_Worn_"+skin.name+".asset";AssetDatabase.DeleteAsset(pathWornMesh);AssetDatabase.CreateAsset(mesh,pathWornMesh);skin.sharedMesh=mesh;
   }
   var wornLod=wornPart.AddComponent<LODGroup>();wornLod.SetLODs(lods);wornLod.RecalculateBounds();
   string wornPath="Assets/Generated/"+spec.id+"_Worn.prefab";PrefabUtility.SaveAsPrefabAsset(instance,wornPath);paths.Add(wornPath);addresses.Add(spec.id+"_Worn");
   report.AppendLine(spec.id+" clips="+animations.Length+" nativeSlot="+part+" triangles="+String.Join("/",skins.Select(s=>(s.sharedMesh.triangles.Length/3).ToString()).ToArray()));UnityEngine.Object.DestroyImmediate(instance);
  }
  AssetDatabase.SaveAssets();
  var bundle=new AssetBundleBuild{assetBundleName="forestarmor.unity3d",assetNames=paths.ToArray(),addressableNames=addresses.ToArray()};if(BuildPipeline.BuildAssetBundles("../Bundle",new[]{bundle},BuildAssetBundleOptions.ChunkBasedCompression,BuildTarget.StandaloneWindows64)==null)throw new Exception("Bundle build failed");
  File.WriteAllText("../unity-build-result.txt","PASS\n"+report);EditorApplication.Exit(0);
 }catch(Exception e){Debug.LogException(e);File.WriteAllText("../unity-build-result.txt","FAIL\n"+e);EditorApplication.Exit(1);}}
}


