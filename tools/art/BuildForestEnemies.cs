using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;
public static class BuildForestEnemies {
 public static void Run() {
  try {
   foreach(string id in new[]{"delveCorruptedWalker","delveImp","delvePossessedSoldier","delveDemonSpawn","delveWarpedBrute","delveAshboundWarden"}) {
   string modelPath="Assets/Creatures/"+id+"/"+id+".fbx";
   AssetDatabase.Refresh();
   var importer=(ModelImporter)AssetImporter.GetAtPath(modelPath);
   importer.animationType=ModelImporterAnimationType.Generic;
   importer.isReadable=true; importer.importCameras=false; importer.importLights=false;
   importer.importAnimation=true; importer.optimizeGameObjects=false;
   importer.animationCompression=ModelImporterAnimationCompression.Off;
   importer.SaveAndReimport();
   var clips=importer.defaultClipAnimations;
   string[] loops={"Idle","Walk","Run","TurnLeft","TurnRight","Corpse","Sleep","LeapAir","Scamper","Brace","Rush","Spent","Windup","Assault","BossRecovery","Withdraw"};
   foreach(var c in clips) { c.name=Short(c.name);c.loopTime=loops.Contains(c.name);c.lockRootPositionXZ=true;c.lockRootHeightY=true;c.lockRootRotation=true; }
   importer.clipAnimations=clips;importer.SaveAndReimport();
   var texImporter=(TextureImporter)AssetImporter.GetAtPath("Assets/Creatures/"+id+"/Albedo.png");
   texImporter.maxTextureSize=2048;texImporter.textureCompression=TextureImporterCompression.CompressedHQ;texImporter.SaveAndReimport();
   Directory.CreateDirectory("Assets/Generated");
   AssetDatabase.DeleteAsset("Assets/Generated/"+id+".mat");
   var material=new Material(Shader.Find("Standard"));material.name=id+"_Surface";
   material.mainTexture=AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Creatures/"+id+"/Albedo.png");
   material.SetFloat("_Glossiness",.15f);material.SetFloat("_Metallic",0);
   material.SetTexture("_EmissionMap",AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Creatures/"+id+"/Emission.png"));material.SetColor("_EmissionColor",Color.white*.5f);material.EnableKeyword("_EMISSION");
   AssetDatabase.CreateAsset(material,"Assets/Generated/"+id+".mat");
   AssetDatabase.DeleteAsset("Assets/Generated/"+id+".controller");
   var controller=AnimatorController.CreateAnimatorControllerAtPath("Assets/Generated/"+id+".controller");
   var animations=AssetDatabase.LoadAllAssetsAtPath(modelPath).OfType<AnimationClip>().Where(c=>!c.name.StartsWith("__preview__")).ToArray();
   foreach(var c in animations) { var state=controller.layers[0].stateMachine.AddState(Short(c.name));state.motion=c;state.writeDefaultValues=true;if(Short(c.name)=="Idle")controller.layers[0].stateMachine.defaultState=state; }
   int expected=id=="delveImp"||id=="delveAshboundWarden"?21:id=="delveWarpedBrute"?20:17; if(animations.Length!=expected)throw new Exception("Expected "+expected+" clips, got "+animations.Length);
   var model=AssetDatabase.LoadAssetAtPath<GameObject>(modelPath);
   var instance=UnityEngine.Object.Instantiate(model);instance.name=id;
   var animator=instance.GetComponent<Animator>();if(animator==null)animator=instance.AddComponent<Animator>();
   animator.runtimeAnimatorController=controller;animator.applyRootMotion=false;animator.cullingMode=AnimatorCullingMode.AlwaysAnimate;
   var skins=instance.GetComponentsInChildren<SkinnedMeshRenderer>(true);
   var lodArray=new LOD[3];
   for(int i=0;i<3;i++) {
    var skin=skins.FirstOrDefault(s=>s.name=="Creature_LOD"+i);if(skin==null)throw new Exception("Missing LOD "+i);
    skin.sharedMaterials=new[]{material};skin.updateWhenOffscreen=true;skin.gameObject.SetActive(true);skin.enabled=true;
    // Expanded bounds cover authored turning, death and rush poses.
    skin.localBounds=new Bounds(new Vector3(0,.9f,0),new Vector3(3.5f,3.5f,3.5f));
    lodArray[i]=new LOD(new[]{.45f,.18f,.025f}[i],new Renderer[]{skin});
   }
   if(skins.Length!=3)throw new Exception("Unexpected mesh count "+skins.Length);
   var lod=instance.GetComponent<LODGroup>();if(lod==null)lod=instance.AddComponent<LODGroup>();lod.SetLODs(lodArray);lod.RecalculateBounds();
   PrefabUtility.SaveAsPrefabAsset(instance,"Assets/Generated/"+id+".prefab");
   UnityEngine.Object.DestroyImmediate(instance);AssetDatabase.SaveAssets();
   string output=Path.GetFullPath("../Bundle");Directory.CreateDirectory(output);
   var build=new AssetBundleBuild{assetBundleName=id.ToLowerInvariant()+".unity3d",assetNames=new[]{"Assets/Generated/"+id+".prefab"},addressableNames=new[]{id}};
   if(BuildPipeline.BuildAssetBundles(output,new[]{build},BuildAssetBundleOptions.ChunkBasedCompression,BuildTarget.StandaloneWindows64)==null)throw new Exception("Build failed");
   File.WriteAllText("../"+id+"-unity-result.txt","PASS\nUnity="+Application.unityVersion+"\nClips="+String.Join(",",animations.Select(c=>c.name+":"+c.length.ToString("F3")).ToArray())+"\nMeshes="+String.Join(",",skins.Select(s=>s==null?"saved":s.name).ToArray()));
   }
   File.WriteAllText("../unity-build-result.txt","PASS\nSix Forest enemies; 113 clips; 18 LOD meshes");EditorApplication.Exit(0);
  }catch(Exception e){Debug.LogException(e);File.WriteAllText("../unity-build-result.txt","FAIL\n"+e);EditorApplication.Exit(1);}
 }
 static string Short(string n){return n.Contains("|")?n.Substring(n.LastIndexOf('|')+1):n;}
}


