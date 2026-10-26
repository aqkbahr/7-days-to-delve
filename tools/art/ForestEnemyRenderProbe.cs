using System;using System.IO;using System.Linq;using System.Collections;using System.Collections.Generic;using System.Text;using UnityEngine;
// Isolated presentation harness. No spawned gameplay entities or combat overrides.
public class ForestEnemyRenderProbe:IModApi {
 static string output;static bool started;
 static string[] ids={"delveCorruptedWalker","delveImp","delvePossessedSoldier","delveDemonSpawn","delveWarpedBrute","delveAshboundWarden"};
 static string[] references={"Boe/ZBoe","Spider/ZSpider","Soldier/ZSoldier","Joe/ZJoe","Hawaiian/ZHawaiian","Biker/ZBiker"};
 static float[] scales={.95f,.75f,1,1,1.12f,1.15f};
 public void InitMod(Mod m){output=Path.GetFullPath(Path.Combine(m.Path,"../.."));ModEvents.UnityUpdate.RegisterHandler(Tick);}
 static void Tick(ref ModEvents.SUnityUpdateData d){if(started||Time.realtimeSinceStartup<35)return;started=true;new GameObject("EnemyReviewRunner").AddComponent<ForestEnemyReviewRunner>().StartCoroutine(Guard());}
 static IEnumerator Guard(){var run=Run();while(true){bool more=false;object current=null;try{more=run.MoveNext();if(more)current=run.Current;}catch(Exception e){File.WriteAllText(Path.Combine(output,"render-result.txt"),"FAIL\n"+e);Log.Error("[EnemyReview] "+e);Application.Quit();yield break;}if(!more)break;yield return current;}Application.Quit();}
 static void Check(bool b,string m){if(!b)throw new Exception(m);}
 static GameObject Load(string id){var p=DataLoader.LoadAsset<GameObject>("#"+Path.Combine(output,"Mods/ForestEnemyRenderProbe/Resources/"+id.ToLowerInvariant()+".unity3d").Replace("\\","/")+"?"+id,true);Check(p!=null,"Missing prefab "+id);var o=UnityEngine.Object.Instantiate(p);foreach(var t in o.GetComponentsInChildren<Transform>(true))t.gameObject.layer=30;o.GetComponent<LODGroup>().ForceLOD(0);return o;}
 static string Short(string n){return n.Contains("|")?n.Substring(n.LastIndexOf('|')+1):n;}
 static IEnumerator Run(){
  var report=new StringBuilder("PASS\nRuntime="+Application.unityVersion+"\nGPU="+SystemInfo.graphicsDeviceName+"\n");
  var cam=new GameObject("EnemyReviewCamera").AddComponent<Camera>();cam.enabled=false;cam.orthographic=true;cam.cullingMask=1<<30;cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.035f,.045f,.055f);cam.nearClipPlane=.01f;cam.farClipPlane=40;
  var light=new GameObject("EnemyReviewLight").AddComponent<Light>();light.type=LightType.Directional;light.cullingMask=1<<30;light.transform.rotation=Quaternion.Euler(35,150,0);RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;
  var overview=Sheet(3,2,512,cam.backgroundColor);var bake=new Mesh();int total=0;
  for(int index=0;index<ids.Length;index++){
   string id=ids[index],dir=Path.Combine(output,id);Directory.CreateDirectory(dir);var o=Load(id);var animator=o.GetComponent<Animator>();animator.speed=0;animator.applyRootMotion=false;
   var skins=o.GetComponentsInChildren<SkinnedMeshRenderer>();Check(skins.Length==3,"LOD count "+id);var skin=skins.Single(s=>s.name=="Creature_LOD0");
   var native=DataLoader.LoadAsset<GameObject>("@:Entities/Zombies/"+references[index]+".prefab",true);Check(native!=null,"Native rig reference");var reference=native.GetComponentsInChildren<Transform>(true).GroupBy(t=>t.name).ToDictionary(g=>g.Key,g=>g.First());
   float error=0;int bones=0;var positions=new StringBuilder();for(int bi=0;bi<skin.bones.Length;bi++){var t=skin.bones[bi];Transform target;if(reference.TryGetValue(t.name,out target)){Vector3 rest=skin.transform.TransformPoint(skin.sharedMesh.bindposes[bi].inverse.MultiplyPoint3x4(Vector3.zero));float d=Vector3.Distance(o.transform.InverseTransformPoint(rest),native.transform.InverseTransformPoint(target.position));error=Mathf.Max(error,d);positions.AppendLine(t.name+" bindRestError="+d.ToString("F6"));bones++;}}
   File.WriteAllText(Path.Combine(dir,"bone-reference-check.txt"),positions.ToString());Check(error<.005f,"Bone reference position "+id+" "+error);Check(bones>50,"Incomplete reference rig");
   Check(skin.sharedMaterial.shader.isSupported&&skin.sharedMaterial.mainTexture!=null,"Material "+id);Check(skin.sharedMaterial.mainTexture.width==2048,"Atlas resolution");
   foreach(var s in skins){Check(s.sharedMesh.boneWeights.All(w=>Mathf.Abs(w.weight0+w.weight1+w.weight2+w.weight3-1)<.01f),"Weights "+s.name);Check(s.sharedMaterials.Length==1,"Material count");Check(s.sharedMesh.triangles.Length/3<=25000,"Triangle budget");if(s!=skin)Check(s.sharedMesh.triangles.Length<skin.sharedMesh.triangles.Length,"Reduced LOD");}
   o.transform.localScale=Vector3.one*scales[index];
   animator.Play("Idle",0,0);animator.Update(0);yield return null;
   Vector3 focus=new Vector3(0,.95f*scales[index],0);cam.orthographicSize=1.27f*scales[index];cam.transform.position=focus+new Vector3(.8f,.25f,3.5f);cam.transform.LookAt(focus);
   light.intensity=1.4f;light.color=new Color(1,.94f,.86f);RenderSettings.ambientLight=new Color(.45f,.45f,.45f);
   var hero=Render(cam,1024);Check(Pixels(hero)>1000,"Blank render "+id);Save(hero,Path.Combine(dir,"game-hero.png"));var thumb=Render(cam,512);overview.SetPixels(index%3*512,(1-index/3)*512,512,512,thumb.GetPixels());UnityEngine.Object.Destroy(thumb);
   foreach(string view in new[]{"front","side","back","night"}){
    cam.transform.position=focus+(view=="side"?new Vector3(3.5f,.15f,0):view=="back"?new Vector3(0,.15f,-3.5f):new Vector3(0,.15f,3.5f));cam.transform.LookAt(focus);
    if(view=="night"){light.intensity=.25f;light.color=new Color(.55f,.7f,1);RenderSettings.ambientLight=new Color(.08f,.10f,.15f);}Save(Render(cam,768),Path.Combine(dir,"game-"+view+".png"));
   }
   light.intensity=1.4f;light.color=new Color(1,.94f,.86f);RenderSettings.ambientLight=new Color(.45f,.45f,.45f);cam.transform.position=focus+new Vector3(.8f,.25f,3.5f);cam.transform.LookAt(focus);cam.orthographicSize=1.5f*scales[index];
   var clips=animator.runtimeAnimatorController.animationClips.OrderBy(c=>Short(c.name)).ToArray();Check(clips.Length==(index==1||index==5?21:index==4?20:17),"Clip count");var sheet=Sheet(6,4,256,cam.backgroundColor);var detail=new StringBuilder();int ci=0;
   foreach(var clip in clips){string state=Short(clip.name);Check(clip.events.Length==0,"Unexpected gameplay event");Check(animator.HasState(0,Animator.StringToHash(state)),"Missing state");
    animator.Play(state,0,.08f);animator.Update(0);skin.BakeMesh(bake);var start=bake.vertices;float delta=0;
    foreach(float time in new[]{.25f,.55f,.85f,1f}){animator.Play(state,0,time);animator.Update(0);skin.BakeMesh(bake);var end=bake.vertices;foreach(var v in end)Check(!float.IsNaN(v.x)&&!float.IsInfinity(v.sqrMagnitude)&&v.sqrMagnitude<36,"Invalid deformed vertex "+id+" "+state);for(int v=0;v<end.Length;v++)delta=Mathf.Max(delta,(end[v]-start[v]).magnitude);}
    if(state!="Corpse")Check(delta>.0001f,"Static motion "+state);else Check(delta<.0001f,"Corpse should be static");
    animator.Play(state,0,.55f);animator.Update(0);yield return null;var frame=Render(cam,256);sheet.SetPixels(ci%6*256,(3-ci/6)*256,256,256,frame.GetPixels());UnityEngine.Object.Destroy(frame);detail.AppendLine((ci+1)+" "+state+" seconds="+clip.length.ToString("F3")+" maxVertexMotion="+delta.ToString("F5"));ci++;total++;
   }
   sheet.Apply();Save(sheet,Path.Combine(dir,"animations-contact-sheet.png"));File.WriteAllText(Path.Combine(dir,"animation-checks-and-order.txt"),detail.ToString());
   animator.Play("Death",0,1);animator.Update(0);skin.BakeMesh(bake);var death=bake.vertices;animator.Play("Corpse",0,0);animator.Update(0);skin.BakeMesh(bake);float corpseError=0;var corpse=bake.vertices;for(int v=0;v<death.Length;v++)corpseError=Mathf.Max(corpseError,(death[v]-corpse[v]).magnitude);Check(corpseError<.001f,"Death/corpse discontinuity "+corpseError);
   // Wake must begin in the dormant pose and finish at idle without a visible snap.
   foreach(string transition in new[]{"SleepWake","WakeIdle"}){animator.Play(transition=="SleepWake"?"Sleep":"Wake",0,transition=="SleepWake"?0:1);animator.Update(0);skin.BakeMesh(bake);var a=bake.vertices;animator.Play(transition=="SleepWake"?"Wake":"Idle",0,0);animator.Update(0);skin.BakeMesh(bake);var b=bake.vertices;float e=0;for(int v=0;v<a.Length;v++)e=Mathf.Max(e,(a[v]-b[v]).magnitude);Check(e<.001f,"Transition discontinuity "+id+" "+transition+" "+e);detail.AppendLine(transition+" endpointError="+e.ToString("F6"));}
   File.WriteAllText(Path.Combine(dir,"animation-checks-and-order.txt"),detail.ToString());
   // Sequential pose strips expose attack/leap anticipation and recovery.
   string[] phases=index==1?new[]{"LeapTakeoff","LeapAir","LeapLand"}:index==4?new[]{"Brace","Rush","Spent"}:index==5?new[]{"Windup","Assault","BossRecovery"}:new[]{"AttackWindup","Attack","Recovery"};
   var strip=Sheet(6,1,256,cam.backgroundColor);for(int i=0;i<6;i++){animator.Play(phases[i/2],0,i%2==0?.2f:.8f);animator.Update(0);yield return null;var f=Render(cam,256);strip.SetPixels(i*256,0,256,256,f.GetPixels());UnityEngine.Object.Destroy(f);}strip.Apply();Save(strip,Path.Combine(dir,"combat-sequence.png"));File.WriteAllText(Path.Combine(dir,"combat-sequence-order.txt"),String.Join(", ",phases)+"; two samples per state at 20% and 80%. Presentation only; no damage events.");
   report.AppendLine(id+" PASS clips="+clips.Length+" nativeBones="+bones+" referencePositionError="+error.ToString("F6")+" deathCorpseError="+corpseError.ToString("F6")+" triangles="+String.Join(",",skins.OrderBy(s=>s.name).Select(s=>(s.sharedMesh.triangles.Length/3).ToString()).ToArray()));UnityEngine.Object.Destroy(o);yield return null;
  }
  overview.Apply();Save(overview,Path.Combine(output,"enemy-overview.png"));File.WriteAllText(Path.Combine(output,"overview-order.txt"),"Left to right, top to bottom: Corrupted Walker, Imp, Possessed Soldier, Demon Spawn, Warped Brute, Ashbound Warden. Each cell framed independently; lineup shows relative size.");
  var lineup=new List<GameObject>();for(int i=0;i<ids.Length;i++){var o=Load(ids[i]);o.transform.position=new Vector3((i-2.5f)*1.5f,0,0);o.transform.localScale=Vector3.one*scales[i];var a=o.GetComponent<Animator>();a.speed=0;a.Play("Idle",0,0);a.Update(0);lineup.Add(o);}yield return null;
  cam.orthographicSize=5.1f;cam.transform.position=new Vector3(0,1.2f,12);cam.transform.LookAt(new Vector3(0,1.1f,0));Save(Render(cam,2048),Path.Combine(output,"enemy-size-lineup.png"));foreach(var o in lineup)UnityEngine.Object.Destroy(o);
  Check(total==113,"Total clips");report.AppendLine("TOTAL six enemies; 113 clips; 18 LOD meshes. No native mesh/texture/animation copied.");report.AppendLine("LIMIT: isolated in-game renderer only. Native AI/controller binding, collider/hitbox/ragdoll behavior, multiplayer and live combat/harvesting acceptance pending. Source size factors applied only to review instances.");File.WriteAllText(Path.Combine(output,"render-result.txt"),report.ToString());
 }
 static Texture2D Sheet(int cols,int rows,int size,Color bg){var t=new Texture2D(cols*size,rows*size,TextureFormat.RGB24,false);var p=new Color[cols*rows*size*size];for(int i=0;i<p.Length;i++)p[i]=bg;t.SetPixels(p);return t;}
 static int Pixels(Texture2D t){int n=0;foreach(var p in t.GetPixels32())if(p.r>30||p.g>32||p.b>35)n++;return n;}
 static void Save(Texture2D t,string path){File.WriteAllBytes(path,t.EncodeToPNG());UnityEngine.Object.Destroy(t);}
 static Texture2D Render(Camera cam,int size){var rt=new RenderTexture(size,size,24);cam.targetTexture=rt;cam.Render();var previous=RenderTexture.active;RenderTexture.active=rt;var t=new Texture2D(size,size,TextureFormat.RGB24,false);t.ReadPixels(new Rect(0,0,size,size),0,0);t.Apply();RenderTexture.active=previous;cam.targetTexture=null;rt.Release();UnityEngine.Object.Destroy(rt);return t;}
}
public class ForestEnemyReviewRunner:MonoBehaviour{}



