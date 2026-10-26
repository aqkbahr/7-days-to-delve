using System;using System.IO;using System.Linq;using System.Collections;using System.Collections.Generic;using System.Text;using UnityEngine;
public class ForestPropRenderProbe:IModApi{
 static string output;static bool started;
 [Serializable]public class Spec{public string id,kind,family;public int clips;public float[] footprint;}
 [Serializable]public class Alias{public string id,target;}
 [Serializable]public class Input{public Spec[] assets;public Alias[] aliases;}
 public void InitMod(Mod m){output=Path.GetFullPath(Path.Combine(m.Path,"../.."));ModEvents.UnityUpdate.RegisterHandler(Tick);}
 static void Tick(ref ModEvents.SUnityUpdateData d){if(started||Time.realtimeSinceStartup<35)return;started=true;new GameObject("PropReviewRunner").AddComponent<ForestPropReviewRunner>().StartCoroutine(Guard());}
 static IEnumerator Guard(){var run=Run();while(true){bool more=false;object current=null;try{more=run.MoveNext();if(more)current=run.Current;}catch(Exception e){File.WriteAllText(Path.Combine(output,"render-result.txt"),"FAIL\n"+e);Log.Error("[PropReview] "+e);Application.Quit();yield break;}if(!more)break;yield return current;}Application.Quit();}
 static void Check(bool c,string s){if(!c)throw new Exception(s);}
 static GameObject Load(string id){var p=DataLoader.LoadAsset<GameObject>("#"+Path.Combine(output,"Mods/ForestPropRenderProbe/Resources/forestprops.unity3d").Replace("\\","/")+"?"+id,true);Check(p!=null,"Missing "+id);var o=UnityEngine.Object.Instantiate(p);foreach(var t in o.GetComponentsInChildren<Transform>(true))t.gameObject.layer=30;return o;}
 static string Short(string n){return n.Contains("|")?n.Substring(n.LastIndexOf('|')+1):n;}
 static IEnumerator Run(){
  var input=Newtonsoft.Json.JsonConvert.DeserializeObject<Input>(File.ReadAllText(Path.Combine(output,"build-input.json")));Check(input.assets.Length==111,"Coverage");
  var report=new StringBuilder("PASS\nRuntime="+Application.unityVersion+"\nGPU="+SystemInfo.graphicsDeviceName+"\n");
  var cam=new GameObject("PropReviewCamera").AddComponent<Camera>();cam.enabled=false;cam.orthographic=true;cam.cullingMask=1<<30;cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.035f,.045f,.055f);cam.nearClipPlane=.01f;cam.farClipPlane=30;
  var light=new GameObject("PropReviewLight").AddComponent<Light>();light.type=LightType.Directional;light.intensity=1.15f;light.color=new Color(1,.94f,.86f);light.cullingMask=1<<30;light.transform.rotation=Quaternion.Euler(35,150,0);RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;RenderSettings.ambientLight=new Color(.35f,.35f,.35f);
  int clipCount=0;var bake=new Mesh();
  foreach(string kind in new[]{"station","plant","item","tool"}){
   var specs=input.assets.Where(s=>s.kind==kind).ToArray();int cols=kind=="item"?6:kind=="tool"?3:4;int rows=(specs.Length+cols-1)/cols;var overview=Sheet(cols,rows,256,cam.backgroundColor);var order=new StringBuilder("Left to right, top to bottom\n");int index=0;
   foreach(var spec in specs){
    var o=Load(spec.id);var animator=o.GetComponent<Animator>();animator.speed=0;animator.applyRootMotion=false;var skins=o.GetComponentsInChildren<SkinnedMeshRenderer>();Check(skins.Length==3,"Skins "+spec.id);var skin=skins.Single(s=>s.name=="Prop_LOD0");o.GetComponent<LODGroup>().ForceLOD(0);
    Check(skin.sharedMaterial.shader.isSupported&&skin.sharedMaterial.mainTexture!=null,"Material "+spec.id);Check(skin.sharedMesh.boneWeights.All(w=>Mathf.Abs(w.weight0+w.weight1+w.weight2+w.weight3-1)<.01f),"Weights "+spec.id);
    animator.Play("Idle",0,0);animator.Update(0);yield return null;skin.BakeMesh(bake);var bounds=bake.bounds;var focus=skin.transform.TransformPoint(bounds.center);cam.orthographicSize=Mathf.Max(.07f,bounds.size.magnitude*.58f);cam.transform.position=focus+new Vector3(1.6f,1.15f,2.7f)*2;cam.transform.LookAt(focus);
    if(kind=="station"||kind=="plant"){
     var collider=o.GetComponent<BoxCollider>();Check(collider!=null,"Interaction collider "+spec.id);Check(collider.isTrigger==(kind=="plant"),"Plant trigger contract");Physics.SyncTransforms();RaycastHit hit;var cb=collider.bounds;Check(Physics.Raycast(cb.center+Vector3.forward*(cb.extents.z+2),Vector3.back,out hit,5,1<<30,QueryTriggerInteraction.Collide)&&hit.collider==collider,"Interaction ray "+spec.id);
     if(kind=="station")Check(cb.size.x<spec.footprint[0]+.04f&&cb.size.y<spec.footprint[1]+.04f&&cb.size.z<spec.footprint[2]+.04f,"Native footprint "+spec.id);
    }
    string dir=Path.Combine(output,spec.id);Directory.CreateDirectory(dir);var hero=Render(cam,768);Check(Pixels(hero)>120,"Blank "+spec.id);Save(hero,Path.Combine(dir,"hero.png"));float originalSize=cam.orthographicSize;
    if(kind=="plant"){float h=spec.family=="Bramble"?.95f:spec.family=="Yarrow"?.60f:spec.family=="Thyme"?.43f:.27f;var rowFocus=new Vector3(0,h*.45f,0);cam.orthographicSize=h*.68f;cam.transform.position=rowFocus+new Vector3(1.6f,1.15f,2.7f)*2;cam.transform.LookAt(rowFocus);}
    var thumb=Render(cam,256);overview.SetPixels(index%cols*256,(rows-1-index/cols)*256,256,256,thumb.GetPixels());UnityEngine.Object.Destroy(thumb);cam.orthographicSize=originalSize;cam.transform.position=focus+new Vector3(1.6f,1.15f,2.7f)*2;cam.transform.LookAt(focus);
    var bg=cam.backgroundColor;cam.backgroundColor=new Color(0,0,0,0);Save(Render(cam,256,true),Path.Combine(dir,"icon.png"));cam.backgroundColor=bg;
    var animations=animator.runtimeAnimatorController.animationClips;Check(animations.Length==spec.clips,"Clips "+spec.id);var details=new StringBuilder();var sheet=Sheet(2,2,256,cam.backgroundColor);int ai=0;
    foreach(var clip in animations){string state=Short(clip.name);Check(clip.events.Length==0,"Gameplay events");animator.Play(state,0,.08f);animator.Update(0);skin.BakeMesh(bake);var start=bake.vertices;animator.Play(state,0,.55f);animator.Update(0);skin.BakeMesh(bake);var end=bake.vertices;float delta=0;
     for(int v=0;v<end.Length;v++){Check(!float.IsNaN(end[v].x)&&!float.IsInfinity(end[v].sqrMagnitude)&&end[v].sqrMagnitude<100,"Invalid vertex "+spec.id+" "+state);delta=Mathf.Max(delta,(end[v]-start[v]).magnitude);}if(state!="Idle"&&state!="Empty"&&state!="Full")Check(delta>.00001f,"Static moving state "+spec.id+" "+state);details.AppendLine(state+" motion="+delta.ToString("F6"));clipCount++;
     if(animations.Length>1){yield return null;var frame=Render(cam,256);sheet.SetPixels(ai%2*256,(1-ai/2)*256,256,256,frame.GetPixels());UnityEngine.Object.Destroy(frame);}ai++;
    }
    if(animations.Length>1){sheet.Apply();Save(sheet,Path.Combine(dir,"states.png"));}else UnityEngine.Object.Destroy(sheet);File.WriteAllText(Path.Combine(dir,"state-checks.txt"),"State sheet: left to right, top to bottom\n"+details);
    if(spec.family=="collector"){
     foreach(string marker in new[]{"InteractionSocket","SpoutSocket","JarSlot1","JarSlot9"})Check(o.GetComponentsInChildren<Transform>().Any(t=>t.name==marker),"Missing collector marker "+marker);
     var gauge=Sheet(2,1,256,cam.backgroundColor);int gi=0;foreach(string state in new[]{"Empty","Full"}){animator.Play(state,0,0);animator.Update(0);yield return null;var target=new Vector3(-.29f,.56f,.418f);cam.orthographicSize=.32f;cam.transform.position=target+new Vector3(0,0,3);cam.transform.LookAt(target);var frame=Render(cam,256);gauge.SetPixels(gi++*256,0,256,256,frame.GetPixels());UnityEngine.Object.Destroy(frame);}gauge.Apply();Save(gauge,Path.Combine(dir,"fill-gauge-empty-full.png"));
    }
    for(int i=0;i<3;i++){var s=skins.Single(v=>v.name=="Prop_LOD"+i);Check(s.sharedMesh.triangles.Length>0,"Empty LOD");if(i>0)Check(s.sharedMesh.triangles.Length<skin.sharedMesh.triangles.Length,"LOD not reduced");}
    var drop=Load(spec.id+"_Drop");Check(drop.GetComponent<MeshFilter>().sharedMesh.vertexCount==skin.sharedMesh.vertexCount,"Drop geometry");Check(drop.GetComponent<BoxCollider>().size.sqrMagnitude>0,"Drop collider");UnityEngine.Object.Destroy(drop);
    report.AppendLine(spec.id+" PASS clips="+animations.Length+" LODs=3 drop=true"+((kind=="station"||kind=="plant")?" interactionRay=true":""));order.AppendLine((index+1)+" "+spec.id);UnityEngine.Object.Destroy(o);index++;yield return null;
   }
   overview.Apply();Save(overview,Path.Combine(output,kind+"-overview.png"));File.WriteAllText(Path.Combine(output,kind+"-order.txt"),order.ToString());
  }
  foreach(var alias in input.aliases){var a=Load(alias.id);var b=Load(alias.target);Check(a.GetComponentsInChildren<SkinnedMeshRenderer>()[0].sharedMesh.vertexCount==b.GetComponentsInChildren<SkinnedMeshRenderer>()[0].sharedMesh.vertexCount,"Alias mismatch");report.AppendLine(alias.id+" alias PASS target="+alias.target);UnityEngine.Object.Destroy(a);UnityEngine.Object.Destroy(b);yield return null;}
  var fxSheet=Sheet(3,1,256,cam.backgroundColor);int fxIndex=0;foreach(string id in new[]{"fxHearthEmbers","fxForgeSmoke","fxCollectorDrip"}){
   var o=Load(id);var ps=o.GetComponent<ParticleSystem>();var main=ps.main;main.stopAction=ParticleSystemStopAction.None;Check(!main.loop&&main.maxParticles<=64,"Effect budget");Check(o.GetComponentsInChildren<Collider>().Length==0&&o.GetComponentsInChildren<Light>().Length==0,"Effect gameplay component");ps.Simulate(.6f,true,true,true);Check(ps.particleCount>0,"Empty effect");cam.orthographicSize=.55f;cam.transform.position=new Vector3(0,.2f,3);cam.transform.LookAt(Vector3.zero);yield return null;var frame=Render(cam,256);Check(Pixels(frame)>3,"Invisible effect "+id);fxSheet.SetPixels(fxIndex*256,0,256,256,frame.GetPixels());Save(frame,Path.Combine(output,id+".png"));ps.Simulate(6,true,true,true);Check(ps.particleCount==0,"Effect expiry");report.AppendLine(id+" PASS visible/expires/no gameplay callbacks");UnityEngine.Object.Destroy(o);yield return null;fxIndex++;
  }fxSheet.Apply();Save(fxSheet,Path.Combine(output,"effects-overview.png"));
  report.AppendLine("TOTAL assets="+input.assets.Length+" clips="+clipCount+" aliases="+input.aliases.Length+" effects=3");report.AppendLine("LIMIT Isolated render, bounds and collider checks. Native placement/crafting/growth/harvest/collector/item actions and multiplayer remain untested.");File.WriteAllText(Path.Combine(output,"render-result.txt"),report.ToString());
 }
 static Texture2D Sheet(int cols,int rows,int size,Color bg){var t=new Texture2D(cols*size,rows*size,TextureFormat.RGB24,false);var p=new Color[cols*rows*size*size];for(int i=0;i<p.Length;i++)p[i]=bg;t.SetPixels(p);return t;}
 static int Pixels(Texture2D t){int n=0;foreach(var p in t.GetPixels32())if(p.r>30||p.g>32||p.b>35)n++;return n;}
 static void Save(Texture2D t,string path){File.WriteAllBytes(path,t.EncodeToPNG());UnityEngine.Object.Destroy(t);}
 static Texture2D Render(Camera cam,int size,bool alpha=false){var rt=new RenderTexture(size,size,24);cam.targetTexture=rt;cam.Render();var previous=RenderTexture.active;RenderTexture.active=rt;var t=new Texture2D(size,size,alpha?TextureFormat.RGBA32:TextureFormat.RGB24,false);t.ReadPixels(new Rect(0,0,size,size),0,0);t.Apply();RenderTexture.active=previous;cam.targetTexture=null;rt.Release();UnityEngine.Object.Destroy(rt);return t;}
}
public class ForestPropReviewRunner:MonoBehaviour{}
