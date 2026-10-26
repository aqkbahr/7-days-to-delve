using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

public static class BuildForestWeapons {
 [Serializable] public class AssetSpec {public string id;public string family;public int clips;public string[] loops;}
 [Serializable] public class Input {public AssetSpec[] assets;}
 [Serializable] public class FxSpec {public string id;public float duration,lifetime,radius,speed,size;public int count;public bool ring;public float[] color;}
 [Serializable] public class FxList {public FxSpec[] effects;}
 static string Short(string n){return n.Contains("|")?n.Substring(n.LastIndexOf('|')+1):n;}
 static float Line(Vector2 p,Vector2 a,Vector2 b){var d=b-a;float t=Mathf.Clamp01(Vector2.Dot(p-a,d)/Mathf.Max(.0001f,d.sqrMagnitude));return Mathf.Exp(-Mathf.Pow((p-a-t*d).magnitude/.06f,2));}
 static float Sprite(string kind,Vector2 p){
  float r=p.magnitude;if(kind=="Soft")return Mathf.Pow(Mathf.Clamp01(1-r),2);
  if(kind=="Ring")return Mathf.Exp(-Mathf.Pow((r-.72f)/.08f,2));
  if(kind=="Spark")return Mathf.Max(Line(p,new Vector2(-.7f,0),new Vector2(.7f,0)),Line(p,new Vector2(0,-.7f),new Vector2(0,.7f)))*Mathf.Clamp01(1-r);
  if(kind=="Flame")return Mathf.Clamp01(1-new Vector2(p.x/(.4f-.15f*p.y),p.y).magnitude);
  Vector2[] points=kind=="Hex"?new[]{new Vector2(0,.65f),new Vector2(.5f,0),new Vector2(0,-.65f),new Vector2(-.5f,0),new Vector2(0,.65f)}:kind=="Ward"?new[]{new Vector2(-.55f,.55f),new Vector2(.55f,.55f),new Vector2(.45f,-.20f),new Vector2(0,-.65f),new Vector2(-.45f,-.20f),new Vector2(-.55f,.55f)}:new[]{new Vector2(-.55f,0),new Vector2(.55f,0),new Vector2(0,0),new Vector2(0,.55f),new Vector2(0,-.55f)};
  float alpha=0;for(int i=0;i<points.Length-1;i++)alpha=Mathf.Max(alpha,Line(p,points[i],points[i+1]));return alpha;
 }
 static FxSpec Fx(string id,Color color,float duration,float life,int count,float radius,float speed,float size,bool ring=false){return new FxSpec{id=id,duration=duration,lifetime=life,count=count,radius=radius,speed=speed,size=size,ring=ring,color=new[]{color.r,color.g,color.b,color.a}};}
 public static void Run(){try{
  AssetDatabase.Refresh();var input=JsonUtility.FromJson<Input>(File.ReadAllText("Assets/build-input.json"));
  Directory.CreateDirectory("Assets/Generated");Directory.CreateDirectory("../Bundle");
  var report=new System.Text.StringBuilder();var paths=new List<string>();var addresses=new List<string>();
  var ti=(TextureImporter)AssetImporter.GetAtPath("Assets/ForestWeaponAtlas.png");ti.maxTextureSize=2048;ti.textureCompression=TextureImporterCompression.CompressedHQ;ti.SaveAndReimport();
  bool rebuilt=File.Exists("Assets/weapon-rebuild.json");AssetDatabase.DeleteAsset("Assets/Generated/ForestWeapon.mat");var material=new Material(Shader.Find(rebuilt?"Delve/WeaponRebuildSurface":"Standard"));material.name="ForestWeaponSurface";material.mainTexture=AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/ForestWeaponAtlas.png");if(!rebuilt)material.SetFloat("_Glossiness",.22f);AssetDatabase.CreateAsset(material,"Assets/Generated/ForestWeapon.mat");
  foreach(string channel in new[]{"Normal","Metallic","Occlusion","Emission"}){
   string tp="Assets/ForestWeapon"+channel+".png";var imp=(TextureImporter)AssetImporter.GetAtPath(tp);imp.maxTextureSize=2048;imp.sRGBTexture=channel=="Emission";imp.textureCompression=TextureImporterCompression.CompressedHQ;imp.alphaSource=TextureImporterAlphaSource.FromInput;
   if(channel=="Normal")imp.textureType=TextureImporterType.NormalMap;imp.SaveAndReimport();
   material.SetTexture(channel=="Normal"?"_BumpMap":channel=="Metallic"?"_MetallicGlossMap":channel=="Occlusion"?"_OcclusionMap":"_EmissionMap",AssetDatabase.LoadAssetAtPath<Texture2D>(tp));
  }
  material.SetFloat("_BumpScale",rebuilt?.35f:.65f);if(!rebuilt){material.EnableKeyword("_NORMALMAP");material.EnableKeyword("_METALLICGLOSSMAP");material.EnableKeyword("_EMISSION");material.SetFloat("_GlossMapScale",1);material.SetFloat("_OcclusionStrength",.7f);material.SetColor("_EmissionColor",Color.white*.22f);}EditorUtility.SetDirty(material);
  foreach(var spec in input.assets){
   string path="Assets/Models/"+spec.id+".fbx";var importer=(ModelImporter)AssetImporter.GetAtPath(path);importer.animationType=ModelImporterAnimationType.Generic;importer.isReadable=true;importer.importCameras=false;importer.importLights=false;importer.optimizeGameObjects=false;importer.animationCompression=ModelImporterAnimationCompression.Off;importer.SaveAndReimport();
   var clips=importer.defaultClipAnimations;foreach(var c in clips){c.name=Short(c.name);c.loopTime=spec.loops.Contains(c.name);c.lockRootPositionXZ=true;c.lockRootHeightY=true;c.lockRootRotation=true;}importer.clipAnimations=clips;importer.SaveAndReimport();
   string cp="Assets/Generated/"+spec.id+".controller";AssetDatabase.DeleteAsset(cp);var controller=AnimatorController.CreateAnimatorControllerAtPath(cp);
   var animations=AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().Where(c=>!c.name.StartsWith("__preview__")).ToArray();
   if(animations.Length!=spec.clips)throw new Exception(spec.id+" clip count "+animations.Length+" expected "+spec.clips);
   foreach(var clip in animations){if(clip.events.Length!=0)throw new Exception("Unexpected animation event");var state=controller.layers[0].stateMachine.AddState(Short(clip.name));state.motion=clip;state.writeDefaultValues=true;if(Short(clip.name)=="Idle")controller.layers[0].stateMachine.defaultState=state;}
   var instance=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(path));instance.name=spec.id;var animator=instance.GetComponent<Animator>();if(animator==null)animator=instance.AddComponent<Animator>();animator.runtimeAnimatorController=controller;animator.applyRootMotion=false;animator.cullingMode=AnimatorCullingMode.AlwaysAnimate;
   var skins=instance.GetComponentsInChildren<SkinnedMeshRenderer>(true);if(skins.Length!=3)throw new Exception(spec.id+" skins="+skins.Length);var lods=new LOD[3];
   for(int i=0;i<3;i++){var skin=skins.Single(s=>s.name=="Weapon_LOD"+i);skin.sharedMaterials=new[]{material};skin.updateWhenOffscreen=true;skin.gameObject.SetActive(true);skin.enabled=true;skin.localBounds=new Bounds(Vector3.zero,Vector3.one*5);lods[i]=new LOD(new[]{.40f,.16f,.02f}[i],new Renderer[]{skin});}
   var lod=instance.GetComponent<LODGroup>();if(lod==null)lod=instance.AddComponent<LODGroup>();lod.SetLODs(lods);lod.RecalculateBounds();
   var weapon=instance.GetComponentsInChildren<Transform>().Single(t=>t.name=="Weapon");
   foreach(string anchor in new[]{"GripRight","GripLeft","Muzzle","EffectOrigin","EdgeBase","EdgeTip"}){
    var source=instance.GetComponentsInChildren<Transform>().Single(t=>t.name==anchor);var socket=new GameObject(anchor+"Socket");socket.transform.SetParent(weapon,false);socket.transform.position=source.position;socket.transform.rotation=instance.transform.rotation;
   }
   string pp="Assets/Generated/"+spec.id+".prefab";PrefabUtility.SaveAsPrefabAsset(instance,pp);paths.Add(pp);addresses.Add(spec.id);
   // Static inventory/drop representation with bounded pickup collider.
   var skin0=skins.Single(s=>s.name=="Weapon_LOD0");var dropMesh=new Mesh();skin0.BakeMesh(dropMesh);var vertices=dropMesh.vertices;for(int v=0;v<vertices.Length;v++)vertices[v]=instance.transform.InverseTransformPoint(skin0.transform.TransformPoint(vertices[v]));dropMesh.vertices=vertices;dropMesh.RecalculateNormals();dropMesh.RecalculateBounds();
   string meshPath="Assets/Generated/"+spec.id+"_Drop.asset";AssetDatabase.DeleteAsset(meshPath);AssetDatabase.CreateAsset(dropMesh,meshPath);var drop=new GameObject(spec.id+"_Drop");drop.AddComponent<MeshFilter>().sharedMesh=dropMesh;drop.AddComponent<MeshRenderer>().sharedMaterial=material;var collider=drop.AddComponent<BoxCollider>();collider.center=dropMesh.bounds.center;collider.size=dropMesh.bounds.size+Vector3.one*.005f;
   string dp="Assets/Generated/"+spec.id+"_Drop.prefab";PrefabUtility.SaveAsPrefabAsset(drop,dp);paths.Add(dp);addresses.Add(spec.id+"_Drop");UnityEngine.Object.DestroyImmediate(drop);
   report.AppendLine(spec.id+" clips="+animations.Length+" triangles="+String.Join("/",skins.Select(s=>(s.sharedMesh.triangles.Length/3).ToString()).ToArray()));UnityEngine.Object.DestroyImmediate(instance);
  }
  // Original procedural particle sprites: no imported art or native game VFX.
  string[] sprites={"Soft","Ring","Spark","Flame","Hex","Heal","Ward"};
  foreach(string sprite in sprites){
   var texture=new Texture2D(128,128,TextureFormat.RGBA32,false);var px=new Color[128*128];for(int y=0;y<128;y++)for(int x=0;x<128;x++){float alpha=Sprite(sprite,new Vector2((x-63.5f)/63.5f,(y-63.5f)/63.5f));px[y*128+x]=new Color(1,1,1,alpha);}texture.SetPixels(px);texture.Apply();string p="Assets/Generated/"+sprite+".png";File.WriteAllBytes(p,texture.EncodeToPNG());UnityEngine.Object.DestroyImmediate(texture);
  }
  AssetDatabase.Refresh();var fxMaterials=new Dictionary<string,Material>();foreach(string sprite in sprites){
   string tp="Assets/Generated/"+sprite+".png";var texImporter=(TextureImporter)AssetImporter.GetAtPath(tp);texImporter.alphaIsTransparency=true;texImporter.wrapMode=TextureWrapMode.Clamp;texImporter.SaveAndReimport();
   string mp="Assets/Generated/Vfx"+sprite+".mat";AssetDatabase.DeleteAsset(mp);var mat=new Material(Shader.Find("Legacy Shaders/Particles/Additive"));mat.mainTexture=AssetDatabase.LoadAssetAtPath<Texture2D>(tp);mat.SetColor("_TintColor",new Color(.5f,.5f,.5f,.5f));AssetDatabase.CreateAsset(mat,mp);fxMaterials[sprite]=mat;
  }
  var spark=new Color(.30f,.65f,1,1);var ember=new Color(1,.32f,.055f,1);var hex=new Color(.65f,.22f,.90f,1);var heal=new Color(.22f,.90f,.48f,1);var ward=new Color(.30f,.80f,.95f,1);var steel=new Color(.9f,.8f,.55f,1);
  var effects=new[]{
   Fx("fxSparkCast",spark,.3f,.25f,16,.035f,1.1f,.05f),Fx("fxSparkImpact",spark,.45f,.35f,28,.07f,1.5f,.06f),
   Fx("fxEmberCast",ember,.4f,.35f,18,.04f,.8f,.10f),Fx("fxEmberImpact",ember,.65f,.5f,28,.1f,1.1f,.15f),Fx("fxEmberBurst",ember,.8f,.65f,64,.1f,2.5f,.18f),
   Fx("fxHexCast",hex,.5f,.4f,14,.035f,.7f,.09f),Fx("fxHexStatus",hex,4.8f,1.2f,8,.4f,.10f,.14f),Fx("fxHexExpire",hex,.4f,.35f,12,.35f,.2f,.07f),
   Fx("fxHealCast",heal,.5f,.4f,18,.04f,.6f,.09f),Fx("fxHealPulse",heal,1.2f,1,24,.45f,.25f,.12f),
   Fx("fxWardCast",ward,.5f,.4f,14,.05f,.4f,.09f),Fx("fxWardStatus",ward,28.5f,1.5f,3,.02f,0,1.1f,true),Fx("fxWardExpire",ward,.6f,.5f,1,.01f,0,1.1f,true),
   Fx("fxRecharge",spark,1.8f,.7f,24,.12f,-.07f,.045f),
   Fx("fxBladeImpact",steel,.25f,.20f,16,.02f,1.5f,.025f),Fx("fxBluntImpact",new Color(.5f,.4f,.28f),.4f,.35f,18,.06f,.7f,.07f),Fx("fxThrustImpact",steel,.3f,.25f,12,.025f,1.3f,.03f),Fx("fxArrowImpact",steel,.3f,.25f,10,.015f,.7f,.025f),
   Fx("fxMeleeSweep",new Color(.60f,.66f,.72f),.22f,.16f,24,.25f,1.5f,.07f),Fx("fxArrowTrail",new Color(.70f,.68f,.56f),2,.15f,60,.005f,0,.015f)
  };
  foreach(var fx in effects){
   var go=new GameObject(fx.id);var ps=go.AddComponent<ParticleSystem>();ps.Stop(true,ParticleSystemStopBehavior.StopEmittingAndClear);var main=ps.main;main.duration=fx.duration;main.loop=false;main.playOnAwake=true;main.startLifetime=fx.lifetime;main.startSpeed=fx.speed;main.startSize=fx.size;main.startColor=new Color(fx.color[0],fx.color[1],fx.color[2],1);main.maxParticles=128;main.simulationSpace=ParticleSystemSimulationSpace.Local;main.stopAction=ParticleSystemStopAction.Destroy;main.useUnscaledTime=false;
   var emission=ps.emission;emission.rateOverTime=0;bool sustained=fx.id.EndsWith("Status")||fx.id=="fxRecharge"||fx.id=="fxArrowTrail";if(sustained)emission.rateOverTime=fx.count;else emission.SetBursts(new[]{new ParticleSystem.Burst(0,(short)fx.count)});
   var shape=ps.shape;shape.shapeType=ParticleSystemShapeType.Sphere;shape.radius=fx.radius;
   if(fx.id=="fxArrowTrail")main.simulationSpace=ParticleSystemSimulationSpace.World;
   if(fx.id=="fxMeleeSweep"){shape.shapeType=ParticleSystemShapeType.Circle;shape.arc=100;}
   var color=ps.colorOverLifetime;color.enabled=true;var gradient=new Gradient();gradient.SetKeys(new[]{new GradientColorKey(Color.white,0),new GradientColorKey(Color.white,1)},new[]{new GradientAlphaKey(0,0),new GradientAlphaKey(1,.12f),new GradientAlphaKey(0,1)});color.color=gradient;
   var size=ps.sizeOverLifetime;size.enabled=true;size.size=new ParticleSystem.MinMaxCurve(1,AnimationCurve.Linear(0,.5f,1,1.1f));
   string sprite=fx.id.Contains("Spark") || (fx.id.EndsWith("Impact") && fx.id!="fxBluntImpact" && fx.id!="fxEmberImpact")?"Spark":fx.id.Contains("Ember")?"Flame":fx.id.Contains("Hex")?"Hex":fx.id.Contains("Heal")?"Heal":fx.id.Contains("Ward")?"Ward":"Soft";
   var renderer=go.GetComponent<ParticleSystemRenderer>();renderer.sharedMaterial=fxMaterials[sprite];renderer.renderMode=ParticleSystemRenderMode.Billboard;renderer.shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.Off;renderer.receiveShadows=false;
   if(fx.id=="fxMeleeSweep"){renderer.renderMode=ParticleSystemRenderMode.Stretch;renderer.lengthScale=2;renderer.velocityScale=.25f;}
   string pp="Assets/Generated/"+fx.id+".prefab";PrefabUtility.SaveAsPrefabAsset(go,pp);paths.Add(pp);addresses.Add(fx.id);UnityEngine.Object.DestroyImmediate(go);report.AppendLine(fx.id+" duration="+fx.duration+" maxParticles=128 no gameplay callbacks");
  }
  File.WriteAllText("../effects-manifest.json",JsonUtility.ToJson(new FxList{effects=effects},true));AssetDatabase.SaveAssets();
  var bundle=new AssetBundleBuild{assetBundleName="forestweapons.unity3d",assetNames=paths.ToArray(),addressableNames=addresses.ToArray()};if(BuildPipeline.BuildAssetBundles("../Bundle",new[]{bundle},BuildAssetBundleOptions.ChunkBasedCompression|BuildAssetBundleOptions.ForceRebuildAssetBundle,BuildTarget.StandaloneWindows64)==null)throw new Exception("Bundle build failed");
  File.WriteAllText("../unity-build-result.txt","PASS\n"+report);EditorApplication.Exit(0);
 }catch(Exception e){Debug.LogException(e);File.WriteAllText("../unity-build-result.txt","FAIL\n"+e);EditorApplication.Exit(1);}}
}
