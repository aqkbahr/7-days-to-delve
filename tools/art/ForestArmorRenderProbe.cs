using System;using System.IO;using System.Linq;using System.Collections;using System.Collections.Generic;using System.Text;using UnityEngine;
public class ForestArmorRenderProbe:IModApi{
 static string output;static bool started;
 [Serializable]public class Spec{public string id,slot,set;public int clips;}
 [Serializable]public class Input{public Spec[] assets;}
 public void InitMod(Mod m){output=Path.GetFullPath(Path.Combine(m.Path,"../.."));ModEvents.UnityUpdate.RegisterHandler(Tick);}
 static void Tick(ref ModEvents.SUnityUpdateData d){if(started||Time.realtimeSinceStartup<35)return;started=true;new GameObject("ArmorReviewRunner").AddComponent<ForestArmorReviewRunner>().StartCoroutine(Guard());}
 static IEnumerator Guard(){var run=Run();while(true){bool more=false;object current=null;try{more=run.MoveNext();if(more)current=run.Current;}catch(Exception e){File.WriteAllText(Path.Combine(output,"render-result.txt"),"FAIL\n"+e);Log.Error("[ArmorReview] "+e);Application.Quit();yield break;}if(!more)break;yield return current;}Application.Quit();}
 static void Check(bool c,string s){if(!c)throw new Exception(s);}
 static GameObject Load(string id){var p=DataLoader.LoadAsset<GameObject>("#"+Path.Combine(output,"Mods/ForestArmorRenderProbe/Resources/forestarmor.unity3d").Replace("\\","/")+"?"+id,true);Check(p!=null,"Missing "+id);var o=UnityEngine.Object.Instantiate(p);foreach(var t in o.GetComponentsInChildren<Transform>(true))t.gameObject.layer=30;return o;}
 static string Short(string n){return n.Contains("|")?n.Substring(n.LastIndexOf('|')+1):n;}
 static IEnumerator Run(){
  var input=Newtonsoft.Json.JsonConvert.DeserializeObject<Input>(File.ReadAllText(Path.Combine(output,"build-input.json")));Check(input.assets.Length==28,"Coverage");
  var report=new StringBuilder("PASS\nRuntime="+Application.unityVersion+"\nGPU="+SystemInfo.graphicsDeviceName+"\n");
  var cam=new GameObject("ArmorReviewCamera").AddComponent<Camera>();cam.enabled=false;cam.orthographic=true;cam.cullingMask=1<<30;cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.035f,.045f,.055f);cam.nearClipPlane=.01f;cam.farClipPlane=30;
  var light=new GameObject("ArmorReviewLight").AddComponent<Light>();light.type=LightType.Directional;light.intensity=1.4f;light.color=new Color(1,.94f,.86f);light.cullingMask=1<<30;light.transform.rotation=Quaternion.Euler(30,150,0);RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;RenderSettings.ambientLight=new Color(.45f,.45f,.45f);
  var native=DataLoader.LoadAsset<GameObject>("@:Entities/Player/Male/Gear/Fiber/gearMaleFiberPrefab.prefab",true);Check(native!=null,"Native skeleton reference");var reference=native.GetComponentsInChildren<Transform>(true).GroupBy(t=>t.name).ToDictionary(g=>g.Key,g=>g.First());
  var pieceSheet=Sheet(4,7,256,cam.backgroundColor);int index=0,clipCount=0;var bake=new Mesh();
  foreach(var spec in input.assets){
   var o=Load(spec.id);var animator=o.GetComponent<Animator>();animator.speed=0;animator.applyRootMotion=false;var skins=o.GetComponentsInChildren<SkinnedMeshRenderer>();Check(skins.Length==3,"Skins "+spec.id);var skin=skins.Single(s=>s.name==spec.slot+"_LOD0");o.GetComponent<LODGroup>().ForceLOD(0);
   float error=0;int bones=0;var positions=new StringBuilder();foreach(var t in o.GetComponentsInChildren<Transform>()){Transform target;if(reference.TryGetValue(t.name,out target)){error=Mathf.Max(error,Vector3.Distance(t.position,target.position));positions.AppendLine(t.name+" custom="+t.position.ToString("F5")+" native="+target.position.ToString("F5"));bones++;}}File.WriteAllText(Path.Combine(output,"bone-reference-check.txt"),positions.ToString());Check(error<.005f,"Reference bone position mismatch "+spec.id+" "+error);
   Check(skin.sharedMaterial.shader.isSupported&&skin.sharedMaterial.mainTexture!=null,"Material "+spec.id);Check(skin.sharedMesh.boneWeights.All(w=>Mathf.Abs(w.weight0+w.weight1+w.weight2+w.weight3-1)<.01f),"Weights "+spec.id);
   animator.Play("Idle",0,0);animator.Update(0);yield return null;skin.BakeMesh(bake);var bounds=bake.bounds;var focus=skin.transform.TransformPoint(bounds.center);cam.orthographicSize=Mathf.Max(.10f,bounds.size.magnitude*.59f);cam.transform.position=focus+new Vector3(1, .5f,3)*2;cam.transform.LookAt(focus);
   string dir=Path.Combine(output,spec.id);Directory.CreateDirectory(dir);var hero=Render(cam,768);Check(Pixels(hero)>300,"Blank "+spec.id);Save(hero,Path.Combine(dir,"hero.png"));var thumb=Render(cam,256);pieceSheet.SetPixels(index%4*256,(6-index/4)*256,256,256,thumb.GetPixels());UnityEngine.Object.Destroy(thumb);
   var bg=cam.backgroundColor;cam.backgroundColor=new Color(0,0,0,0);o.SetActive(false);var iconDrop=Load(spec.id+"_Drop");var iconBounds=iconDrop.GetComponent<MeshFilter>().sharedMesh.bounds;cam.orthographicSize=Mathf.Max(.1f,iconBounds.size.magnitude*.60f);cam.transform.position=iconBounds.center+new Vector3(1,.5f,3)*2;cam.transform.LookAt(iconBounds.center);Save(Render(cam,256,true),Path.Combine(dir,"icon.png"));UnityEngine.Object.Destroy(iconDrop);o.SetActive(true);cam.backgroundColor=bg;
   var animations=animator.runtimeAnimatorController.animationClips;Check(animations.Length==7,"Clips "+spec.id);float maxMotion=0;var detail=new StringBuilder();
   foreach(var clip in animations){string state=Short(clip.name);Check(clip.events.Length==0,"Gameplay events");animator.Play(state,0,.08f);animator.Update(0);skin.BakeMesh(bake);var start=bake.vertices;
    animator.Play(state,0,.55f);animator.Update(0);skin.BakeMesh(bake);var end=bake.vertices;float delta=0;for(int v=0;v<end.Length;v++){Check(!float.IsNaN(end[v].x)&&!float.IsInfinity(end[v].sqrMagnitude)&&end[v].sqrMagnitude<25,"Invalid vertex "+spec.id+" "+state);delta=Mathf.Max(delta,(end[v]-start[v]).magnitude);}maxMotion=Mathf.Max(maxMotion,delta);detail.AppendLine(state+" motion="+delta.ToString("F5"));clipCount++;
   }
   Check(maxMotion>.001f,"No deformation "+spec.id);for(int i=0;i<3;i++){var s=skins.Single(v=>v.name==spec.slot+"_LOD"+i);Check(s.sharedMesh.triangles.Length>0,"Empty LOD");if(i>0)Check(s.sharedMesh.triangles.Length<skin.sharedMesh.triangles.Length,"LOD not reduced");}
   var drop=Load(spec.id+"_Drop");Check(drop.GetComponent<MeshFilter>().sharedMesh.vertexCount==skin.sharedMesh.vertexCount,"Drop geometry");Check(drop.GetComponent<BoxCollider>().size.sqrMagnitude>0,"Drop collider");UnityEngine.Object.Destroy(drop);
   File.WriteAllText(Path.Combine(dir,"pose-checks.txt"),detail.ToString());report.AppendLine(spec.id+" PASS clips=7 LODs=3 drop=true bones="+bones+" referenceError="+error.ToString("F6"));UnityEngine.Object.Destroy(o);index++;yield return null;
  }
  pieceSheet.Apply();Save(pieceSheet,Path.Combine(output,"pieces-overview.png"));
  string[] sets={"Light","Medium","Heavy","Padded","ForgedLight","ForgedMedium","ForgedHeavy","MixedClothIron","MixedLeatherForged","MixedPaddedLight"};string[] states={"Idle","Walk","Run","Crouch","Attack","Cast","Grip"};var overview=Sheet(4,3,512,cam.backgroundColor);var order=new StringBuilder();index=0;
  var mannequin=new Material(Shader.Find("Standard"));mannequin.color=new Color(.28f,.29f,.28f);
  foreach(string set in sets){
   var objects=new List<GameObject>();int part=0;string[] variants=set=="MixedClothIron"?new[]{"Heavy","Light","Medium","Heavy"}:set=="MixedLeatherForged"?new[]{"ForgedMedium","Medium","ForgedHeavy","ForgedLight"}:set=="MixedPaddedLight"?new[]{"Light","Padded","ForgedLight","Medium"}:new[]{set,set,set,set};foreach(string slot in new[]{"Helmet","Outfit","Gloves","Boots"})objects.Add(Load("armorDelve"+variants[part++]+slot));
   foreach(var o in objects){o.GetComponent<LODGroup>().ForceLOD(0);o.GetComponent<Animator>().speed=0;}
   // Original neutral QA head/neck primitives. Not an exported native character mesh.
   var head=GameObject.CreatePrimitive(PrimitiveType.Sphere);head.name="Original_QA_Head";head.layer=30;head.transform.SetParent(objects[1].GetComponentsInChildren<Transform>().Single(t=>t.name=="Head"),false);head.transform.localPosition=new Vector3(0,.05f,.012f);head.transform.localScale=new Vector3(.18f,.245f,.20f);head.GetComponent<Renderer>().sharedMaterial=mannequin;
   var neck=GameObject.CreatePrimitive(PrimitiveType.Cylinder);neck.name="Original_QA_Neck";neck.layer=30;neck.transform.SetParent(objects[1].GetComponentsInChildren<Transform>().Single(t=>t.name=="Neck"),false);neck.transform.localPosition=new Vector3(0,.045f,0);neck.transform.localScale=new Vector3(.10f,.085f,.10f);neck.GetComponent<Renderer>().sharedMaterial=mannequin;
   var sheet=Sheet(3,3,384,cam.backgroundColor);int pose=0;string dir=Path.Combine(output,set);Directory.CreateDirectory(dir);
   foreach(string state in states){foreach(var o in objects){var a=o.GetComponent<Animator>();a.Play(state,0,state=="Idle"?0:.32f);a.Update(0);}yield return null;
    var focus=new Vector3(0,.94f,0);cam.orthographicSize=1.04f;cam.transform.position=focus+new Vector3(.8f,.2f,3.5f);cam.transform.LookAt(focus);var frame=Render(cam,384);sheet.SetPixels(pose%3*384,(2-pose/3)*384,384,384,frame.GetPixels());UnityEngine.Object.Destroy(frame);
    if(state=="Idle"){Save(Render(cam,1024),Path.Combine(dir,"hero.png"));var thumb=Render(cam,512);overview.SetPixels(index%4*512,(2-index/4)*512,512,512,thumb.GetPixels());UnityEngine.Object.Destroy(thumb);}pose++;
   }
   foreach(var o in objects){var a=o.GetComponent<Animator>();a.Play("Idle",0,0);a.Update(0);}yield return null;
   foreach(var angle in new[]{new Vector3(3.5f,.2f,0),new Vector3(-.8f,.2f,-3.5f)}){var focus=new Vector3(0,.94f,0);cam.transform.position=focus+angle;cam.transform.LookAt(focus);var frame=Render(cam,384);sheet.SetPixels(pose%3*384,(2-pose/3)*384,384,384,frame.GetPixels());UnityEngine.Object.Destroy(frame);pose++;}
   sheet.Apply();Save(sheet,Path.Combine(dir,"poses.png"));File.WriteAllText(Path.Combine(dir,"pose-order.txt"),"Left to right, top to bottom: Idle, Walk, Run, Crouch, Attack, Cast, Grip, side, rear.\nOriginal fitting motions; not native combat animation replacements.");
   foreach(var o in objects)UnityEngine.Object.Destroy(o);yield return null;order.AppendLine((index+1)+" "+set);report.AppendLine("SET "+set+" PASS assembled four pieces, seven poses, side/rear");index++;
  }
  overview.Apply();Save(overview,Path.Combine(output,"armor-overview.png"));File.WriteAllText(Path.Combine(output,"overview-order.txt"),order.ToString());report.AppendLine("TOTAL pieces=28 clips="+clipCount+" sets=7 mixedSets=3");report.AppendLine("LIMIT Render and original pose checks only. Native SDCS attachment, body morphs/hair masks, first-person hands and live equip/combat remain pending.");File.WriteAllText(Path.Combine(output,"render-result.txt"),report.ToString());
 }
 static Texture2D Sheet(int cols,int rows,int size,Color bg){var t=new Texture2D(cols*size,rows*size,TextureFormat.RGB24,false);var p=new Color[cols*rows*size*size];for(int i=0;i<p.Length;i++)p[i]=bg;t.SetPixels(p);return t;}
 static int Pixels(Texture2D t){int n=0;foreach(var p in t.GetPixels32())if(p.r>30||p.g>32||p.b>35)n++;return n;}
 static void Save(Texture2D t,string path){File.WriteAllBytes(path,t.EncodeToPNG());UnityEngine.Object.Destroy(t);}
 static Texture2D Render(Camera cam,int size,bool alpha=false){var rt=new RenderTexture(size,size,24);cam.targetTexture=rt;cam.Render();var previous=RenderTexture.active;RenderTexture.active=rt;var t=new Texture2D(size,size,alpha?TextureFormat.RGBA32:TextureFormat.RGB24,false);t.ReadPixels(new Rect(0,0,size,size),0,0);t.Apply();RenderTexture.active=previous;cam.targetTexture=null;rt.Release();UnityEngine.Object.Destroy(rt);return t;}
}
public class ForestArmorReviewRunner:MonoBehaviour{}
