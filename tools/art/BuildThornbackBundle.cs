using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;
public static class BuildThornbackBundle {
 public static void Run() {
  try {
   const string modelPath="Assets/Thornback/delveThornbackBoar.fbx";
   AssetDatabase.Refresh();
   var importer=(ModelImporter)AssetImporter.GetAtPath(modelPath);
   importer.animationType=ModelImporterAnimationType.Generic;
   importer.isReadable=true; importer.importCameras=false; importer.importLights=false;
   importer.importAnimation=true; importer.optimizeGameObjects=false;
   importer.animationCompression=ModelImporterAnimationCompression.Off;
   importer.SaveAndReimport();
   var clips=importer.defaultClipAnimations;
   string[] loops={"Idle","Walk","Run","TurnLeft","TurnRight","Brace","Rush","Recovery","Corpse","Sleep"};
   foreach(var c in clips) { c.name=Short(c.name);c.loopTime=loops.Contains(c.name);c.lockRootPositionXZ=true;c.lockRootHeightY=true;c.lockRootRotation=true; }
   importer.clipAnimations=clips;importer.SaveAndReimport();
   var texImporter=(TextureImporter)AssetImporter.GetAtPath("Assets/Thornback/Thornback_Albedo.png");
   texImporter.maxTextureSize=2048;texImporter.textureCompression=TextureImporterCompression.CompressedHQ;texImporter.SaveAndReimport();
   Directory.CreateDirectory("Assets/Generated");
   AssetDatabase.DeleteAsset("Assets/Generated/Thornback.mat");
   var material=new Material(Shader.Find("Standard"));material.name="Thornback_BarkHide";
   material.mainTexture=AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Thornback/Thornback_Albedo.png");
   material.SetFloat("_Glossiness",.15f);material.SetFloat("_Metallic",0);
   AssetDatabase.CreateAsset(material,"Assets/Generated/Thornback.mat");
   AssetDatabase.DeleteAsset("Assets/Generated/Thornback.controller");
   var controller=AnimatorController.CreateAnimatorControllerAtPath("Assets/Generated/Thornback.controller");
   var animations=AssetDatabase.LoadAllAssetsAtPath(modelPath).OfType<AnimationClip>().Where(c=>!c.name.StartsWith("__preview__")).ToArray();
   foreach(var c in animations) { var state=controller.layers[0].stateMachine.AddState(Short(c.name));state.motion=c;state.writeDefaultValues=true;if(Short(c.name)=="Idle")controller.layers[0].stateMachine.defaultState=state; }
   if(animations.Length!=18)throw new Exception("Expected 18 clips, got "+animations.Length);
   var model=AssetDatabase.LoadAssetAtPath<GameObject>(modelPath);
   var instance=UnityEngine.Object.Instantiate(model);instance.name="delveThornbackBoar";
   var animator=instance.GetComponent<Animator>();if(animator==null)animator=instance.AddComponent<Animator>();
   animator.runtimeAnimatorController=controller;animator.applyRootMotion=false;animator.cullingMode=AnimatorCullingMode.AlwaysAnimate;
   var skins=instance.GetComponentsInChildren<SkinnedMeshRenderer>(true);
   var lodArray=new LOD[3];
   for(int i=0;i<3;i++) {
    var skin=skins.FirstOrDefault(s=>s.name=="Thornback_LOD"+i);if(skin==null)throw new Exception("Missing LOD "+i);
    skin.sharedMaterials=new[]{material};skin.updateWhenOffscreen=true;skin.gameObject.SetActive(true);skin.enabled=true;
    // Expanded bounds cover authored turning, death and rush poses.
    skin.localBounds=new Bounds(new Vector3(0,.5f,0),new Vector3(2.5f,2.5f,2.8f));
    lodArray[i]=new LOD(new[]{.45f,.18f,.025f}[i],new Renderer[]{skin});
   }
   if(skins.Length!=3)throw new Exception("Unexpected mesh count "+skins.Length);
   var lod=instance.GetComponent<LODGroup>();if(lod==null)lod=instance.AddComponent<LODGroup>();lod.SetLODs(lodArray);lod.RecalculateBounds();
   PrefabUtility.SaveAsPrefabAsset(instance,"Assets/Generated/delveThornbackBoar.prefab");
   UnityEngine.Object.DestroyImmediate(instance);AssetDatabase.SaveAssets();
   string output=Path.GetFullPath("../Bundle");Directory.CreateDirectory(output);
   var build=new AssetBundleBuild{assetBundleName="thornback.unity3d",assetNames=new[]{"Assets/Generated/delveThornbackBoar.prefab"},addressableNames=new[]{"delveThornbackBoar"}};
   if(BuildPipeline.BuildAssetBundles(output,new[]{build},BuildAssetBundleOptions.ChunkBasedCompression,BuildTarget.StandaloneWindows64)==null)throw new Exception("Build failed");
   File.WriteAllText("../unity-build-result.txt","PASS\nUnity="+Application.unityVersion+"\nClips="+String.Join(",",animations.Select(c=>c.name+":"+c.length.ToString("F3")).ToArray())+"\nMeshes="+String.Join(",",skins.Select(s=>s==null?"saved":s.name).ToArray()));
   EditorApplication.Exit(0);
  }catch(Exception e){Debug.LogException(e);File.WriteAllText("../unity-build-result.txt","FAIL\n"+e);EditorApplication.Exit(1);}
 }
 static string Short(string n){return n.Contains("|")?n.Substring(n.LastIndexOf('|')+1):n;}
}
