using System;
using System.Collections;
using System.IO;
using System.Text;
using UnityEngine;
using DelveThornback;
public class ThornbackRenderProbe : IModApi {
 static string output;static bool done;
 public void InitMod(Mod m){output=Path.GetFullPath(Path.Combine(m.Path,"../.."));ModEvents.UnityUpdate.RegisterHandler(Tick);}
 static void Tick(ref ModEvents.SUnityUpdateData d){if(done || Time.realtimeSinceStartup<35)return;done=true;new GameObject("ThornbackRenderRunner").AddComponent<ThornbackRenderRunner>().StartCoroutine(Guard());}
 static IEnumerator Guard(){var run=Run();while(true){bool more=false;object current=null;try{more=run.MoveNext();if(more)current=run.Current;}catch(Exception e){File.WriteAllText(Path.Combine(output,"render-result.txt"),"FAIL\n"+e);Log.Error("[ThornbackRender] "+e);Application.Quit();yield break;}if(!more)break;yield return current;}Application.Quit();}
 static void Require(bool c,string m){if(!c)throw new Exception(m);}
 static IEnumerator Run(){
  var instance=UnityEngine.Object.Instantiate(ModApi.GetPrefab());
  instance.transform.position=Vector3.zero;instance.transform.rotation=Quaternion.identity;
  foreach(var t in instance.GetComponentsInChildren<Transform>(true))t.gameObject.layer=30;
  var lod=instance.GetComponent<LODGroup>();lod.ForceLOD(0);
  var animator=instance.GetComponent<Animator>();animator.cullingMode=AnimatorCullingMode.AlwaysAnimate;animator.applyRootMotion=false;
  var skin=Array.Find(instance.GetComponentsInChildren<SkinnedMeshRenderer>(),s=>s.name=="Thornback_LOD0");
  Require(skin!=null,"Missing skin");Require(skin.bones.Length>=35,"Incomplete bones");
  Require(skin.sharedMaterial.shader.isSupported,"Shader unsupported");
  Require(skin.sharedMaterial.mainTexture!=null,"Texture missing");
  var cameraObject=new GameObject("ThornbackPreviewCamera");var cam=cameraObject.AddComponent<Camera>();cam.enabled=false;
  cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.035f,.045f,.055f);cam.cullingMask=1<<30;cam.fieldOfView=34;cam.nearClipPlane=.05f;cam.farClipPlane=20;
  cam.transform.position=new Vector3(1.7f,1.2f,2.45f);cam.transform.LookAt(new Vector3(0,.55f,0));
  RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;RenderSettings.ambientLight=new Color(.45f,.45f,.45f);
  var lightObject=new GameObject("ThornbackPreviewLight");var light=lightObject.AddComponent<Light>();light.type=LightType.Directional;light.intensity=1.3f;light.color=new Color(1,.91f,.78f);light.cullingMask=1<<30;lightObject.transform.rotation=Quaternion.Euler(35,-35,0);
  string[] states={"Idle","Walk","Run","TurnLeft","TurnRight","Alert","Scrape","Brace","Rush","Brake","Recovery","Attack","AttackRunning","Hit","Death","Corpse","Sleep","Wake"};
  var report=new StringBuilder("PASS\nRuntime="+Application.unityVersion+"\nGraphics="+SystemInfo.graphicsDeviceName+"\nBones="+skin.bones.Length+"\nTriangles="+skin.sharedMesh.triangles.Length/3+"\n");
  var sheet=new Texture2D(6*256,3*256,TextureFormat.RGB24,false);
  var baked=new Mesh();
  for(int i=0;i<states.Length;i++) {
   Require(animator.HasState(0,Animator.StringToHash(states[i])),"Missing state "+states[i]);
   animator.Play(states[i],0,.08f);animator.Update(0);skin.BakeMesh(baked);var start=baked.vertices;
   animator.Play(states[i],0,.55f);animator.Update(0);skin.BakeMesh(baked);var end=baked.vertices;
   float delta=0;var bounds=new Bounds(skin.transform.TransformPoint(end[0]),Vector3.zero);
   for(int v=0;v<end.Length;v++){Require(!float.IsNaN(end[v].x),"Invalid vertex");delta=Mathf.Max(delta,(end[v]-start[v]).magnitude);bounds.Encapsulate(skin.transform.TransformPoint(end[v]));}
   Require(bounds.size.magnitude<5 && bounds.size.magnitude>.5f,"Invalid animated bounds "+states[i]+" "+bounds);
   if(states[i]!="Corpse")Require(delta>.0001f,"Animation does not deform mesh "+states[i]);
   animator.speed=0;yield return null;
   var frame=Render(cam,256);sheet.SetPixels((i%6)*256,(2-i/6)*256,256,256,frame.GetPixels());UnityEngine.Object.Destroy(frame);
   report.AppendLine(states[i]+" maxVertexMotion="+delta.ToString("F5")+" bounds="+bounds.size);
  }
  sheet.Apply();File.WriteAllBytes(Path.Combine(output,"animations-contact-sheet.png"),sheet.EncodeToPNG());
  animator.Play("Idle",0,0);animator.Update(0);yield return null;
  string[] names={"hero","front","side","back","night"};
  Vector3[] positions={new Vector3(1.7f,1.2f,2.45f),new Vector3(0,.9f,2.9f),new Vector3(2.9f,.9f,0),new Vector3(0,.9f,-2.9f),new Vector3(1.7f,1.2f,2.45f)};
  for(int i=0;i<names.Length;i++) {
   cam.transform.position=positions[i];cam.transform.LookAt(new Vector3(0,.55f,0));
   if(names[i]=="night"){light.intensity=.25f;light.color=new Color(.55f,.7f,1);RenderSettings.ambientLight=new Color(.08f,.10f,.15f);}
   var frame=Render(cam,1024);File.WriteAllBytes(Path.Combine(output,"game-"+names[i]+".png"),frame.EncodeToPNG());UnityEngine.Object.Destroy(frame);
  }
  foreach(var s in instance.GetComponentsInChildren<SkinnedMeshRenderer>())report.AppendLine("LOD "+s.name+" triangles="+s.sharedMesh.triangles.Length/3);
  File.WriteAllText(Path.Combine(output,"render-result.txt"),report.ToString());Log.Out("[ThornbackRender] PASS 18 clips, skin deformation, 3 LODs and rendered views");
 }
 static Texture2D Render(Camera cam,int size){var rt=new RenderTexture(size,size,24);cam.targetTexture=rt;cam.Render();var previous=RenderTexture.active;RenderTexture.active=rt;var texture=new Texture2D(size,size,TextureFormat.RGB24,false);texture.ReadPixels(new Rect(0,0,size,size),0,0);texture.Apply();RenderTexture.active=previous;cam.targetTexture=null;rt.Release();UnityEngine.Object.Destroy(rt);return texture;}
}
public class ThornbackRenderRunner:MonoBehaviour {}
