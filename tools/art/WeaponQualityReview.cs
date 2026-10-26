using System;using System.IO;using System.Linq;using UnityEngine;using UnityEditor;
public static class WeaponQualityReview {
 public static void Run(){try{
  string output=Path.GetFullPath("../QualityReview");Directory.CreateDirectory(output);var report=new System.Text.StringBuilder();
  var cam=new GameObject("ReviewCamera").AddComponent<Camera>();cam.orthographic=true;cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.035f,.045f,.055f);cam.nearClipPlane=.01f;cam.farClipPlane=30;
  RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;RenderSettings.ambientLight=new Color(.4f,.4f,.4f);
  var cube=new Cubemap(32,TextureFormat.RGBA32,false);for(int f=0;f<6;f++){var px=new Color[1024];for(int y=0;y<32;y++)for(int x=0;x<32;x++)px[y*32+x]=Color.Lerp(new Color(.14f,.17f,.20f),new Color(.75f,.78f,.82f),Mathf.Exp(-Mathf.Pow((x-14)/5f,2))*.7f+(f==2?.2f:0));cube.SetPixels(px,(CubemapFace)f);}cube.Apply();RenderSettings.defaultReflectionMode=UnityEngine.Rendering.DefaultReflectionMode.Custom;RenderSettings.customReflectionTexture=cube;
  var key=new GameObject("Key").AddComponent<Light>();key.type=LightType.Directional;key.intensity=1.25f;key.color=new Color(1,.92f,.82f);key.transform.rotation=Quaternion.Euler(30,-30,0);
  var fill=new GameObject("Fill").AddComponent<Light>();fill.type=LightType.Directional;fill.intensity=.45f;fill.color=new Color(.65f,.78f,1);fill.transform.rotation=Quaternion.Euler(20,125,0);
  var input=JsonUtility.FromJson<BuildForestWeapons.Input>(File.ReadAllText("Assets/build-input.json"));var baked=new Mesh();int clips=0;
  foreach(var spec in input.assets){
   var obj=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Generated/"+spec.id+".prefab"));obj.GetComponent<LODGroup>().ForceLOD(0);var animator=obj.GetComponent<Animator>();animator.enabled=false;
   var skin=obj.GetComponentsInChildren<SkinnedMeshRenderer>().Single(s=>s.name=="Weapon_LOD0");var animations=animator.runtimeAnimatorController.animationClips;
   foreach(var clip in animations){clip.SampleAnimation(obj,.3f*clip.length);skin.BakeMesh(baked);if(baked.vertices.Any(v=>float.IsNaN(v.x)||v.sqrMagnitude>36))throw new Exception("Invalid skin "+spec.id);clips++;}
   animations.First(c=>c.name.EndsWith("Idle")).SampleAnimation(obj,0);skin.BakeMesh(baked);var bounds=baked.bounds;Vector3 focus=skin.transform.TransformPoint(bounds.center);cam.orthographicSize=Mathf.Max(.08f,bounds.size.magnitude*.6f);
   string dir=Path.Combine(output,spec.id);Directory.CreateDirectory(dir);
   for(int view=0;view<3;view++){cam.transform.position=focus+new[]{new Vector3(1.3f,1.1f,2.6f),new Vector3(-1.4f,.3f,2.6f),new Vector3(.2f,.8f,-2.8f)}[view]*2;cam.transform.LookAt(focus);Render(cam,Path.Combine(dir,"view-"+view+".png"),1024);}
   report.AppendLine(spec.id+" triangles="+skin.sharedMesh.triangles.Length/3+" clips="+animations.Length+" three views PASS");UnityEngine.Object.DestroyImmediate(obj);
  }
  File.WriteAllText(Path.Combine(output,"result.txt"),"PASS models="+input.assets.Length+" clips="+clips+"\n"+report);EditorApplication.Exit(0);
 }catch(Exception e){File.WriteAllText("../QualityReview/result.txt","FAIL\n"+e);Debug.LogException(e);EditorApplication.Exit(1);}}
 static void Render(Camera cam,string path,int size){var rt=new RenderTexture(size,size,24);cam.targetTexture=rt;cam.Render();RenderTexture.active=rt;var tex=new Texture2D(size,size,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,size,size),0,0);tex.Apply();File.WriteAllBytes(path,tex.EncodeToPNG());RenderTexture.active=null;cam.targetTexture=null;UnityEngine.Object.DestroyImmediate(tex);rt.Release();UnityEngine.Object.DestroyImmediate(rt);}
}
