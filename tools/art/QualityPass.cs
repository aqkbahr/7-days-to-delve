using System;using System.IO;using System.Linq;using System.Collections.Generic;using UnityEngine;using UnityEditor;
public static class QualityPass {
 [Serializable] public class Spec {public string id,group,kind,slot,blend,fbx,texture,prefab,destination,bundle;public float[] native_footprint;}
 [Serializable] public class Input {public Spec[] models;}
 [Serializable] public class Result {public string texture_id;public int actions,bones;public bool native_foundation;}
 [Serializable] public class Alias {public string id,target;}
 [Serializable] public class AliasInput {public Alias[] aliases;}
 static Dictionary<string,Material> materials=new Dictionary<string,Material>();
 static Dictionary<string,Dictionary<string,string>> bundles=new Dictionary<string,Dictionary<string,string>>();
 static string Output;static Camera camera;static System.Text.StringBuilder report=new System.Text.StringBuilder();
 static void Check(bool condition,string reason){if(!condition)throw new Exception(reason);}
 static void SaveMesh(Mesh mesh,string path){var old=AssetDatabase.LoadAssetAtPath<Mesh>(path);if(old==null)AssetDatabase.CreateAsset(mesh,path);else{EditorUtility.CopySerialized(mesh,old);UnityEngine.Object.DestroyImmediate(mesh);}}
 static Material Material(string id){
  Material result;if(materials.TryGetValue(id,out result))return result;
  string folder="Assets/QualitySurfaces/"+id;
  foreach(string channel in new[]{"Albedo","Normal","Metallic","Occlusion","Emission"}){
   var ti=(TextureImporter)AssetImporter.GetAtPath(folder+"/"+channel+".png");Check(ti!=null,"Missing map "+id+"/"+channel);ti.sRGBTexture=channel=="Albedo"||channel=="Emission";ti.maxTextureSize=2048;ti.textureCompression=TextureImporterCompression.CompressedHQ;ti.anisoLevel=4;if(channel=="Normal")ti.textureType=TextureImporterType.NormalMap;ti.SaveAndReimport();
  }
  string path="Assets/QualityMaterials/"+id+".mat";result=AssetDatabase.LoadAssetAtPath<Material>(path);if(result==null){result=new Material(Shader.Find("Delve/QualitySurface"));AssetDatabase.CreateAsset(result,path);}result.shader=Shader.Find("Delve/QualitySurface");
  string[] names={"Albedo","Normal","Metallic","Occlusion","Emission"},props={"_MainTex","_BumpMap","_MetallicGlossMap","_OcclusionMap","_EmissionMap"};
  for(int i=0;i<names.Length;i++)result.SetTexture(props[i],AssetDatabase.LoadAssetAtPath<Texture2D>(folder+"/"+names[i]+".png"));result.SetFloat("_BumpScale",.65f);EditorUtility.SetDirty(result);materials[id]=result;return result;
 }
 static void Add(string bundle,string address,string path){if(!bundles.ContainsKey(bundle))bundles[bundle]=new Dictionary<string,string>();bundles[bundle][address]=path;}
 static void Studio(){
  camera=new GameObject("QualityCamera").AddComponent<Camera>();camera.enabled=false;camera.orthographic=true;camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.045f,.055f,.065f);camera.nearClipPlane=.01f;camera.farClipPlane=100;
  RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;RenderSettings.ambientLight=new Color(.38f,.38f,.38f);
  var cube=new Cubemap(32,TextureFormat.RGBA32,false);for(int f=0;f<6;f++){var px=new Color[1024];for(int y=0;y<32;y++)for(int x=0;x<32;x++)px[y*32+x]=Color.Lerp(new Color(.14f,.17f,.20f),new Color(.72f,.76f,.80f),Mathf.Exp(-Mathf.Pow((x-14)/5f,2))*.65f+(f==2?.15f:0));cube.SetPixels(px,(CubemapFace)f);}cube.Apply();RenderSettings.defaultReflectionMode=UnityEngine.Rendering.DefaultReflectionMode.Custom;RenderSettings.customReflectionTexture=cube;
  var key=new GameObject("Key").AddComponent<Light>();key.type=LightType.Directional;key.intensity=1.1f;key.color=new Color(1,.94f,.87f);key.transform.rotation=Quaternion.Euler(35,-30,0);
  var fill=new GameObject("Fill").AddComponent<Light>();fill.type=LightType.Directional;fill.intensity=.5f;fill.color=new Color(.7f,.82f,1);fill.transform.rotation=Quaternion.Euler(20,140,0);
 }
 static void Render(GameObject obj,string folder){
  Directory.CreateDirectory(folder);var skins=obj.GetComponentsInChildren<SkinnedMeshRenderer>();var bounds=new Bounds();bool first=true;
  foreach(var skin in skins){if(!skin.name.EndsWith("LOD0"))continue;var baked=new Mesh();skin.BakeMesh(baked);foreach(var v in baked.vertices){var p=skin.transform.TransformPoint(v);if(first){bounds=new Bounds(p,Vector3.zero);first=false;}else bounds.Encapsulate(p);}UnityEngine.Object.DestroyImmediate(baked);}
  if(first)foreach(var r in obj.GetComponentsInChildren<Renderer>()){if(first){bounds=r.bounds;first=false;}else bounds.Encapsulate(r.bounds);}
  Check(!first,"No render bounds "+obj.name);camera.orthographicSize=Mathf.Max(.07f,bounds.size.magnitude*.60f);
  var vectors=new[]{new Vector3(1.3f,.65f,2.6f),new Vector3(-1.7f,.25f,2.5f),new Vector3(.8f,.6f,-2.7f)};
  for(int i=0;i<3;i++){
   camera.transform.position=bounds.center+vectors[i]*Mathf.Max(2,bounds.size.magnitude);camera.transform.LookAt(bounds.center);var rt=new RenderTexture(768,768,24);camera.targetTexture=rt;camera.Render();RenderTexture.active=rt;var pic=new Texture2D(768,768,TextureFormat.RGB24,false);pic.ReadPixels(new Rect(0,0,768,768),0,0);pic.Apply();File.WriteAllBytes(Path.Combine(folder,"view-"+i+".png"),pic.EncodeToPNG());RenderTexture.active=null;camera.targetTexture=null;UnityEngine.Object.DestroyImmediate(pic);rt.Release();UnityEngine.Object.DestroyImmediate(rt);
  }
 }
 static void Process(Spec spec,bool full){
  string evidence=Path.Combine(spec.destination,"quality.json");if(!File.Exists(evidence)){if(full)throw new Exception("Source incomplete "+spec.id);return;}
  var result=JsonUtility.FromJson<Result>(File.ReadAllText(evidence));var material=Material(result.texture_id);Check(material.shader.isSupported,"Unsupported quality shader");
  string modelPath="Assets/Legacy/"+spec.group+"/"+spec.fbx;var importer=(ModelImporter)AssetImporter.GetAtPath(modelPath);importer.isReadable=true;importer.importCameras=false;importer.importLights=false;importer.animationCompression=ModelImporterAnimationCompression.Off;importer.SaveAndReimport();
  var source=AssetDatabase.LoadAssetAtPath<GameObject>(spec.prefab);Check(source!=null,"Missing prefab "+spec.prefab);var obj=UnityEngine.Object.Instantiate(source);obj.name=spec.id;
  if(result.native_foundation){var marker=new GameObject("DelveNativeBodyFoundation_v1");marker.transform.SetParent(obj.transform,false);}
  var skins=obj.GetComponentsInChildren<SkinnedMeshRenderer>(true);Check(skins.Length==3,"Expected 3 skins "+spec.id);foreach(var skin in skins){Check(skin.sharedMesh!=null,"Null skin "+spec.id);skin.sharedMaterial=material;Check(skin.sharedMesh.colors.Length==skin.sharedMesh.vertexCount,"Missing painted occlusion "+spec.id);Check(skin.sharedMesh.tangents.Length==skin.sharedMesh.vertexCount,"Missing tangents "+spec.id);}
  var animator=obj.GetComponent<Animator>();Check(animator!=null&&animator.runtimeAnimatorController!=null,"Missing animator "+spec.id);animator.enabled=false;var clips=animator.runtimeAnimatorController.animationClips;Check(clips.Length==result.actions,"Clip contract changed "+spec.id+" "+clips.Length+"/"+result.actions);
  var bake=new Mesh();foreach(var clip in clips){Check(clip.events.Length==0,"Gameplay animation events "+spec.id);foreach(float t in new[]{0f,.5f,1f}){clip.SampleAnimation(obj,clip.length*t);foreach(var s in skins){s.BakeMesh(bake);Check(bake.vertices.All(v=>!float.IsNaN(v.x)&&!float.IsInfinity(v.x)&&v.sqrMagnitude<100),"Invalid deformed skin "+spec.id+" "+clip.name);}}}
  clips.First(c=>c.name.EndsWith("Idle")).SampleAnimation(obj,0);animator.enabled=true;obj.GetComponent<LODGroup>().ForceLOD(-1);
  string folder="Assets/QualityPrefabs/"+spec.group;Directory.CreateDirectory(folder);string path=folder+"/"+spec.id+".prefab";PrefabUtility.SaveAsPrefabAsset(obj,path);Add(spec.bundle,spec.id,path);
  var skin0=skins.Single(s=>s.name==spec.slot+"_LOD0");string oldDrop="Assets/Legacy/"+spec.group+"/Generated/"+spec.id+"_Drop.prefab";
  if(AssetDatabase.LoadAssetAtPath<GameObject>(oldDrop)!=null){
   skin0.BakeMesh(bake);var dropMesh=UnityEngine.Object.Instantiate(bake);var vs=dropMesh.vertices;for(int i=0;i<vs.Length;i++){vs[i]=obj.transform.InverseTransformPoint(skin0.transform.TransformPoint(vs[i]));if(spec.group=="armor"&&spec.slot=="Gloves")vs[i].x-=Mathf.Sign(vs[i].x)*.42f;}dropMesh.vertices=vs;dropMesh.RecalculateBounds();if(spec.group!="weapons"){var center=dropMesh.bounds.center;for(int i=0;i<vs.Length;i++)vs[i]-=center;dropMesh.vertices=vs;dropMesh.RecalculateBounds();}
   string mp=folder+"/"+spec.id+"_Drop.asset";SaveMesh(dropMesh,mp);var drop=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(oldDrop));drop.GetComponent<MeshFilter>().sharedMesh=AssetDatabase.LoadAssetAtPath<Mesh>(mp);drop.GetComponent<MeshRenderer>().sharedMaterial=material;var collider=drop.GetComponent<BoxCollider>();collider.center=drop.GetComponent<MeshFilter>().sharedMesh.bounds.center;collider.size=drop.GetComponent<MeshFilter>().sharedMesh.bounds.size+Vector3.one*.005f;string dp=folder+"/"+spec.id+"_Drop.prefab";PrefabUtility.SaveAsPrefabAsset(drop,dp);Add(spec.bundle,spec.id+"_Drop",dp);UnityEngine.Object.DestroyImmediate(drop);
  }
  if(spec.group=="armor"){
   var worn=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Legacy/armor/Generated/"+spec.id+"_Worn.prefab"));var boneMap=worn.GetComponentsInChildren<Transform>(true).GroupBy(t=>t.name).ToDictionary(g=>g.Key,g=>g.First());
   foreach(var target in worn.GetComponentsInChildren<SkinnedMeshRenderer>(true)){
    var original=skins.Single(s=>s.name==target.name);var mesh=UnityEngine.Object.Instantiate(original.sharedMesh);var weights=mesh.boneWeights;var used=new SortedSet<int>();foreach(var w in weights){if(w.weight0>0)used.Add(w.boneIndex0);if(w.weight1>0)used.Add(w.boneIndex1);if(w.weight2>0)used.Add(w.boneIndex2);if(w.weight3>0)used.Add(w.boneIndex3);}var indices=used.ToArray();var map=new Dictionary<int,int>();for(int j=0;j<indices.Length;j++)map[indices[j]]=j;
    for(int j=0;j<weights.Length;j++){var w=weights[j];w.boneIndex0=w.weight0>0?map[w.boneIndex0]:0;w.boneIndex1=w.weight1>0?map[w.boneIndex1]:0;w.boneIndex2=w.weight2>0?map[w.boneIndex2]:0;w.boneIndex3=w.weight3>0?map[w.boneIndex3]:0;weights[j]=w;}var poses=mesh.bindposes;mesh.boneWeights=weights;mesh.bindposes=indices.Select(j=>poses[j]).ToArray();target.bones=indices.Select(j=>boneMap[original.bones[j].name]).ToArray();target.sharedMaterial=material;string mp=folder+"/"+spec.id+"_Worn_"+target.name+".asset";SaveMesh(mesh,mp);target.sharedMesh=AssetDatabase.LoadAssetAtPath<Mesh>(mp);
   }string wp=folder+"/"+spec.id+"_Worn.prefab";PrefabUtility.SaveAsPrefabAsset(worn,wp);Add(spec.bundle,spec.id+"_Worn",wp);UnityEngine.Object.DestroyImmediate(worn);
  }
  obj.GetComponent<LODGroup>().ForceLOD(0);animator.enabled=false;Render(obj,Path.Combine(Output,spec.group,spec.id));report.AppendLine(spec.id+" PASS clips="+clips.Length+" LODs=3 triangles="+skin0.sharedMesh.triangles.Length/3+" paintedAO=true");UnityEngine.Object.DestroyImmediate(bake);UnityEngine.Object.DestroyImmediate(obj);
 }
 static void Batch(Spec spec){
  var source=AssetDatabase.LoadAssetAtPath<GameObject>(spec.prefab);Check(source!=null,"Missing batch prefab "+spec.prefab);var obj=UnityEngine.Object.Instantiate(source);obj.name=spec.id;string folder="Assets/QualityPrefabs/"+spec.group;Directory.CreateDirectory(folder);
  foreach(var renderer in obj.GetComponentsInChildren<MeshRenderer>(true)){
   var old=renderer.sharedMaterial;string label=old.name;string key=spec.group+"_"+label;Material material;
   if(!materials.TryGetValue(key,out material)){
    material=new Material(Material("props"));material.name=key;int tile=label.Contains("Iron")?2:label.Contains("Linen")?5:label.Contains("Resin")?9:0;
    material.mainTextureScale=Vector2.one*.235f;material.mainTextureOffset=new Vector2((tile%4+.03f)/4,(tile/4+.03f)/4);string mp="Assets/QualityMaterials/"+key+".mat";AssetDatabase.DeleteAsset(mp);AssetDatabase.CreateAsset(material,mp);materials[key]=material;
   }renderer.sharedMaterial=material;
   var filter=renderer.GetComponent<MeshFilter>();var mesh=UnityEngine.Object.Instantiate(filter.sharedMesh);var colors=new Color[mesh.vertexCount];var v=mesh.vertices;var n=mesh.normals;
   for(int i=0;i<v.Length;i++){float shade=.93f+.06f*Mathf.Sin(v[i].x*31+v[i].z*19)*Mathf.Sin(v[i].y*27);colors[i]=new Color(shade,shade,shade,Mathf.Lerp(.80f,1,(n[i].y+1)*.5f));}mesh.colors=colors;mesh.RecalculateTangents();string path=folder+"/"+spec.id+"_"+renderer.name+".asset";SaveMesh(mesh,path);filter.sharedMesh=AssetDatabase.LoadAssetAtPath<Mesh>(path);
  }
  Check(obj.GetComponentsInChildren<Collider>().Length==source.GetComponentsInChildren<Collider>().Length,"Batch collider changed");string pp=folder+"/"+spec.id+".prefab";PrefabUtility.SaveAsPrefabAsset(obj,pp);Add(spec.bundle,spec.id,pp);Render(obj,Path.Combine(Output,spec.group,spec.id));report.AppendLine(spec.group+"/"+spec.id+" PASS materials, colored wear, preserved colliders");UnityEngine.Object.DestroyImmediate(obj);
 }
 static void BuildBundles(){
  var aliases=JsonUtility.FromJson<AliasInput>(File.ReadAllText("Assets/Legacy/props/build-input.json"));if(aliases.aliases!=null)foreach(var alias in aliases.aliases){
   string target="Assets/QualityPrefabs/props/"+alias.target+".prefab";var obj=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(target));obj.name=alias.id;string path="Assets/QualityPrefabs/props/"+alias.id+".prefab";PrefabUtility.SaveAsPrefabAsset(obj,path);Add("forestprops.unity3d",alias.id,path);UnityEngine.Object.DestroyImmediate(obj);
  }
  foreach(string group in new[]{"weapons","props"})foreach(string path in Directory.GetFiles("Assets/Legacy/"+group+"/Generated","fx*.prefab"))Add("forest"+group+".unity3d",Path.GetFileNameWithoutExtension(path),path.Replace('\\','/'));
  AssetDatabase.SaveAssets();Directory.CreateDirectory("../Bundles");var builds=bundles.Select(kv=>new AssetBundleBuild{assetBundleName=kv.Key,assetNames=kv.Value.Values.ToArray(),addressableNames=kv.Value.Keys.ToArray()}).ToArray();
  Check(BuildPipeline.BuildAssetBundles("../Bundles",builds,BuildAssetBundleOptions.ChunkBasedCompression,BuildTarget.StandaloneWindows64)!=null,"Bundle build failed");
  File.WriteAllText("../Reports/bundle-addresses.txt",String.Join("\n",bundles.SelectMany(kv=>kv.Value.Keys.Select(k=>kv.Key+"?"+k)).ToArray()));report.AppendLine("BUNDLES "+builds.Length+" original addresses retained");
 }
 public static void Run(){try{Output=Path.GetFullPath("../Review");Directory.CreateDirectory(Output);Directory.CreateDirectory("Assets/QualityMaterials");Directory.CreateDirectory("Assets/QualityPrefabs");AssetDatabase.Refresh();Studio();report.AppendLine("NATIVE_FOUNDATION_HELPER PASS checks="+NativeFoundationChecks.Run());var input=JsonUtility.FromJson<Input>(File.ReadAllText("../inventory.json"));bool full=File.Exists("../Reports/build-all.flag");foreach(var spec in input.models)if(!String.IsNullOrEmpty(spec.blend))Process(spec,full);else if(full)Batch(spec);if(full)BuildBundles();AssetDatabase.SaveAssets();File.WriteAllText("../Reports/unity-review.txt","PASS\n"+report);EditorApplication.Exit(0);}catch(Exception e){Debug.LogException(e);File.WriteAllText("../Reports/unity-review.txt","FAIL\n"+e+"\n"+report);EditorApplication.Exit(1);}}
}
