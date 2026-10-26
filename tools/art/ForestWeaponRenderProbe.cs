using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
public class ForestWeaponRenderProbe:IModApi {
 static string output;static bool started;
 [Serializable] public class Spec {public string id,family;public int clips;}
 [Serializable] public class Input {public Spec[] assets;}
 [Serializable] public class Fx {public string id;public float duration,lifetime,radius,speed,size;public int count;}
 [Serializable] public class FxInput {public Fx[] effects;}
 public void InitMod(Mod mod){output=Path.GetFullPath(Path.Combine(mod.Path,"../.."));ModEvents.UnityUpdate.RegisterHandler(Tick);}
 static void Tick(ref ModEvents.SUnityUpdateData d){if(started || Time.realtimeSinceStartup<35)return;started=true;new GameObject("WeaponReviewRunner").AddComponent<ForestWeaponReviewRunner>().StartCoroutine(Guard());}
 static IEnumerator Guard(){var run=Run();while(true){bool more=false;object current=null;try{more=run.MoveNext();if(more)current=run.Current;}catch(Exception e){File.WriteAllText(Path.Combine(output,"render-result.txt"),"FAIL\n"+e);Log.Error("[WeaponReview] "+e);Application.Quit();yield break;}if(!more)break;yield return current;}Application.Quit();}
 static void Check(bool c,string text){if(!c)throw new Exception(text);}
 static GameObject Load(string id){var prefab=DataLoader.LoadAsset<GameObject>("#"+Path.Combine(output,"Mods/ForestWeaponRenderProbe/Resources/forestweapons.unity3d").Replace("\\","/")+"?"+id,true);Check(prefab!=null,"Missing prefab "+id);var o=UnityEngine.Object.Instantiate(prefab);foreach(var t in o.GetComponentsInChildren<Transform>(true))t.gameObject.layer=30;return o;}
 static string Short(string n){return n.Contains("|")?n.Substring(n.LastIndexOf('|')+1):n;}
 static IEnumerator Run(){
  var inputs=Newtonsoft.Json.JsonConvert.DeserializeObject<Input>(File.ReadAllText(Path.Combine(output,"build-input.json")));var fxInputs=Newtonsoft.Json.JsonConvert.DeserializeObject<FxInput>(File.ReadAllText(Path.Combine(output,"effects-manifest.json")));
  Check(inputs!=null && inputs.assets!=null,"Asset input failed to deserialize");Check(fxInputs!=null && fxInputs.effects!=null,"Effect input failed to deserialize");var specs=inputs.assets;var effects=fxInputs.effects;
  var report=new StringBuilder("PASS\nRuntime="+Application.unityVersion+"\nGPU="+SystemInfo.graphicsDeviceName+"\n");
  var go=new GameObject("WeaponReviewCamera");var cam=go.AddComponent<Camera>();cam.enabled=false;cam.orthographic=true;cam.cullingMask=1<<30;cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.035f,.045f,.055f);cam.nearClipPlane=.01f;cam.farClipPlane=30;
  var lightObject=new GameObject("WeaponReviewLight");var light=lightObject.AddComponent<Light>();light.type=LightType.Directional;light.intensity=1.25f;light.color=new Color(1,.92f,.82f);light.cullingMask=1<<30;lightObject.transform.rotation=Quaternion.Euler(30,-30,0);RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;RenderSettings.ambientLight=new Color(.4f,.4f,.4f);
  var nativePaths=new[]{"@:Other/Items/Weapons/Melee/Knives/hunting_knifePrefab.prefab","@:Other/Items/Weapons/Melee/ClubWood/clubWoodPrefab.prefab","@:Other/Items/Weapons/Melee/Spear/spear_iron_Prefab.prefab","@:Other/Items/Weapons/Ranged/Bows/advancedBow/advancedWoodenBow/advancedWoodenBowPrefab.prefab","@:Other/Items/Weapons/Ranged/IronCrossBow/ironCrossBowPrefab.prefab"};
  var environment=new Cubemap(32,TextureFormat.RGBA32,false);foreach(CubemapFace face in new[]{CubemapFace.PositiveX,CubemapFace.NegativeX,CubemapFace.PositiveY,CubemapFace.NegativeY,CubemapFace.PositiveZ,CubemapFace.NegativeZ}){var pixels=new Color[1024];for(int y=0;y<32;y++)for(int x=0;x<32;x++){float strip=Mathf.Exp(-Mathf.Pow((x-14)/5f,2));pixels[y*32+x]=Color.Lerp(new Color(.14f,.17f,.20f),new Color(.75f,.78f,.82f),strip*.7f+(face==CubemapFace.PositiveY?.2f:0));}environment.SetPixels(pixels,face);}environment.Apply();RenderSettings.defaultReflectionMode=UnityEngine.Rendering.DefaultReflectionMode.Custom;RenderSettings.customReflection=environment;RenderSettings.reflectionIntensity=1;
  var fillObject=new GameObject("WeaponReviewFill");var fill=fillObject.AddComponent<Light>();fill.type=LightType.Directional;fill.intensity=.45f;fill.color=new Color(.65f,.78f,1);fill.cullingMask=1<<30;fillObject.transform.rotation=Quaternion.Euler(20,125,0);
  var nativeNames=new[]{"hunting-knife","wooden-club","iron-spear","wooden-bow","iron-crossbow"};
  for(int ni=0;ni<nativePaths.Length;ni++){
   var prefab=DataLoader.LoadAsset<GameObject>(nativePaths[ni],true);Check(prefab!=null,"Native reference "+nativeNames[ni]);var native=UnityEngine.Object.Instantiate(prefab);foreach(var tr in native.GetComponentsInChildren<Transform>(true))tr.gameObject.layer=30;
   foreach(var anim in native.GetComponentsInChildren<Animator>(true))anim.enabled=false;
   // The stock shader needs world globals absent in a menu-only probe. Normalize
   // reference lighting with temporary Standard materials; never alter native assets.
   foreach(var renderer in native.GetComponentsInChildren<Renderer>(true)){
    var mats=renderer.sharedMaterials;for(int mi=0;mi<mats.Length;mi++){var original=mats[mi];if(original==null)continue;report.AppendLine("REFERENCE_PROPERTIES "+nativeNames[ni]+" "+String.Join(",",original.GetTexturePropertyNames()));var neutral=new Material(Shader.Find("Standard"));neutral.mainTexture=original.mainTexture;neutral.SetFloat("_Glossiness",.35f);foreach(string prop in new[]{"_BumpMap","_MetallicGlossMap","_OcclusionMap"})if(original.HasProperty(prop)&&original.GetTexture(prop)!=null){neutral.SetTexture(prop,original.GetTexture(prop));if(prop=="_BumpMap")neutral.EnableKeyword("_NORMALMAP");if(prop=="_MetallicGlossMap")neutral.EnableKeyword("_METALLICGLOSSMAP");}mats[mi]=neutral;}renderer.sharedMaterials=mats;
   }
   var rs=native.GetComponentsInChildren<Renderer>();Check(rs.Length>0,"Native renderers");var nb=rs[0].bounds;foreach(var r in rs)nb.Encapsulate(r.bounds);
   cam.orthographicSize=Mathf.Max(.08f,nb.size.magnitude*.65f);cam.transform.position=nb.center+new Vector3(1.3f,1.1f,2.6f)*2;cam.transform.LookAt(nb.center);yield return null;
   var pic=Render(cam,1024);File.WriteAllBytes(Path.Combine(output,"native-"+nativeNames[ni]+".png"),pic.EncodeToPNG());UnityEngine.Object.Destroy(pic);
   foreach(var r in rs)foreach(var m in r.sharedMaterials)if(m!=null)report.AppendLine("REFERENCE "+nativeNames[ni]+" shader="+m.shader.name+" albedo="+(m.mainTexture==null?"none":m.mainTexture.width+"x"+m.mainTexture.height));UnityEngine.Object.Destroy(native);
  }
  int index=0,totalClips=0;var overview=Sheet(5,4,256,cam.backgroundColor);var ammo=Sheet(5,4,256,cam.backgroundColor);var baked=new Mesh();
  foreach(var spec in specs){
   string dir=Path.Combine(output,spec.id);Directory.CreateDirectory(dir);var o=Load(spec.id);var animator=o.GetComponent<Animator>();animator.cullingMode=AnimatorCullingMode.AlwaysAnimate;animator.applyRootMotion=false;animator.speed=0;var lod=o.GetComponent<LODGroup>();Check(lod!=null,"Missing LOD "+spec.id);lod.ForceLOD(0);
   var skins=o.GetComponentsInChildren<SkinnedMeshRenderer>();Check(skins.Length==3,"LOD count "+spec.id);var skin=Array.Find(skins,s=>s.name=="Weapon_LOD0");Check(skin.sharedMaterial.shader.isSupported && skin.sharedMaterial.mainTexture!=null,"Material "+spec.id);
   foreach(string map in new[]{"_BumpMap","_MetallicGlossMap","_OcclusionMap","_EmissionMap"})Check(skin.sharedMaterial.GetTexture(map)!=null,"Missing PBR "+map+" "+spec.id);
   Check(skin.sharedMesh.triangles.Length/3<16000,"Triangle budget "+spec.id);Check(skin.sharedMesh.tangents.Length==skin.sharedMesh.vertexCount,"Normal map tangents "+spec.id);
   foreach(string marker in new[]{"GripRightSocket","GripLeftSocket","MuzzleSocket","EffectOriginSocket","EdgeTipSocket"})Check(Array.Exists(o.GetComponentsInChildren<Transform>(),t=>t.name==marker),"Missing anchor "+spec.id+" "+marker);
   animator.Play("Idle",0,0);animator.Update(0);yield return null;skin.BakeMesh(baked);var bounds=baked.bounds;var focus=skin.transform.TransformPoint(bounds.center);cam.orthographicSize=Mathf.Max(.08f,bounds.size.magnitude*.65f);cam.transform.position=focus+new Vector3(1.3f,1.1f,2.6f)*2;cam.transform.LookAt(focus);
   var hero=Render(cam,768);Check(Pixels(hero)>300,"Blank model "+spec.id);File.WriteAllBytes(Path.Combine(dir,"hero.png"),hero.EncodeToPNG());UnityEngine.Object.Destroy(hero);var thumb=Render(cam,256);var target=index<20?overview:ammo;int cell=index<20?index:index-20;target.SetPixels((cell%5)*256,(3-cell/5)*256,256,256,thumb.GetPixels());UnityEngine.Object.Destroy(thumb);
   // Icons are a neutral inspect angle with transparent background, not native item assignment.
   var old=cam.backgroundColor;cam.backgroundColor=new Color(0,0,0,0);var icon=Render(cam,256,true);File.WriteAllBytes(Path.Combine(dir,"icon.png"),icon.EncodeToPNG());UnityEngine.Object.Destroy(icon);cam.backgroundColor=old;
   cam.orthographicSize*=1.4f;
   var animations=animator.runtimeAnimatorController.animationClips;Check(animations.Length==spec.clips,"Clips "+spec.id);totalClips+=animations.Length;var sheet=Sheet(3,3,256,cam.backgroundColor);var states=new List<string>();var details=new StringBuilder();int frameIndex=0;
   foreach(var clip in animations){
    string state=Short(clip.name);states.Add(state);Check(clip.events.Length==0,"Unexpected gameplay event");Check(animator.HasState(0,Animator.StringToHash(state)),"Missing state "+state);
    animator.Play(state,0,.08f);animator.Update(0);skin.BakeMesh(baked);var start=baked.vertices;animator.Play(state,0,.55f);animator.Update(0);skin.BakeMesh(baked);var end=baked.vertices;float delta=0;
    foreach(var v in end)Check(!float.IsNaN(v.x)&&!float.IsInfinity(v.x)&&v.sqrMagnitude<36,"Invalid skin vertex "+spec.id+" "+state);
    for(int i=0;i<end.Length;i++)delta=Mathf.Max(delta,(end[i]-start[i]).magnitude);
    bool accessory=spec.family=="rune"||spec.family=="arrow"||spec.family=="bolt";if(!accessory && state!="Hold")Check(delta>.00001f,"No animation motion "+spec.id+" "+state);
    yield return null;var frame=Render(cam,256);sheet.SetPixels((frameIndex%3)*256,(2-frameIndex/3)*256,256,256,frame.GetPixels());UnityEngine.Object.Destroy(frame);frameIndex++;details.AppendLine(state+" motion="+delta.ToString("F6"));
   }
   sheet.Apply();File.WriteAllBytes(Path.Combine(dir,"animations.png"),sheet.EncodeToPNG());File.WriteAllText(Path.Combine(dir,"states.txt"),"Left to right, top to bottom\n"+String.Join(", ",states.ToArray())+"\n"+details);
   for(int i=0;i<skins.Length;i++)Check(skins[i].sharedMesh.triangles.Length>0,"Empty LOD");
   var drop=Load(spec.id+"_Drop");Check(drop.GetComponent<MeshFilter>().sharedMesh.vertexCount==skin.sharedMesh.vertexCount,"Drop geometry "+spec.id);Check(drop.GetComponent<BoxCollider>().size.sqrMagnitude>0,"Drop collider "+spec.id);UnityEngine.Object.Destroy(drop);
   report.AppendLine(spec.id+" PASS clips="+animations.Length+" LODs=3 drop=true vertices="+skin.sharedMesh.vertexCount);UnityEngine.Object.Destroy(sheet);UnityEngine.Object.Destroy(o);yield return null;index++;
  }
  overview.Apply();ammo.Apply();File.WriteAllBytes(Path.Combine(output,"weapons-overview.png"),overview.EncodeToPNG());File.WriteAllBytes(Path.Combine(output,"ammunition-overview.png"),ammo.EncodeToPNG());UnityEngine.Object.Destroy(overview);UnityEngine.Object.Destroy(ammo);
  var fxSheet=Sheet(5,4,256,cam.backgroundColor);index=0;
  foreach(var fx in effects){
   var o=Load(fx.id);Check(o.GetComponentsInChildren<Collider>().Length==0 && o.GetComponentsInChildren<Light>().Length==0,"Effect gameplay collider/light "+fx.id);var ps=o.GetComponent<ParticleSystem>();var main=ps.main;main.stopAction=ParticleSystemStopAction.None;Check(!main.loop && main.maxParticles<=128,"Effect budget "+fx.id);Check(o.GetComponent<ParticleSystemRenderer>().sharedMaterial.shader.isSupported,"VFX shader "+fx.id);
   float sample=fx.id.EndsWith("Status")?.7f:Mathf.Min(fx.lifetime*.5f,.3f);ps.Simulate(sample,true,true,true);
   if(fx.id=="fxArrowTrail"){ps.Simulate(0,true,true,true);for(int step=0;step<15;step++){o.transform.position=new Vector3(-.6f+step*.08f,0,0);ps.Simulate(1f/60,true,false,true);}}
   Check(ps.particleCount>0,"Empty effect "+fx.id);int live=ps.particleCount;
   cam.orthographicSize=fx.id=="fxArrowTrail"?1:fx.id=="fxEmberBurst"?2.2f:Mathf.Max(.25f,fx.radius+fx.speed*sample+fx.size*2);cam.transform.position=new Vector3(0,.15f,4);cam.transform.LookAt(Vector3.zero);yield return null;
   var frame=Render(cam,256);Check(Pixels(frame)>5,"Invisible effect "+fx.id);fxSheet.SetPixels((index%5)*256,(3-index/5)*256,256,256,frame.GetPixels());File.WriteAllBytes(Path.Combine(output,fx.id+".png"),frame.EncodeToPNG());UnityEngine.Object.Destroy(frame);
   ps.Simulate(fx.duration+fx.lifetime+1,true,true,true);Check(ps.particleCount==0,"Effect does not expire "+fx.id);report.AppendLine(fx.id+" PASS liveParticles="+live+" expires=true");UnityEngine.Object.Destroy(o);yield return null;index++;
  }
  fxSheet.Apply();File.WriteAllBytes(Path.Combine(output,"effects-overview.png"),fxSheet.EncodeToPNG());report.AppendLine("TOTAL models="+specs.Length+" clips="+totalClips+" effects="+effects.Length);report.AppendLine("LIMIT Standalone prop/particle rendering, not native player-hand fitting, gameplay hook or multiplayer acceptance.");File.WriteAllText(Path.Combine(output,"render-result.txt"),report.ToString());
 }
 static Texture2D Sheet(int cols,int rows,int size,Color bg){var t=new Texture2D(cols*size,rows*size,TextureFormat.RGB24,false);var p=new Color[cols*rows*size*size];for(int i=0;i<p.Length;i++)p[i]=bg;t.SetPixels(p);return t;}
 static int Pixels(Texture2D t){int n=0;foreach(var p in t.GetPixels32())if(p.r>30 || p.g>32 || p.b>35)n++;return n;}
 static Texture2D Render(Camera cam,int size,bool alpha=false){var rt=new RenderTexture(size,size,24);cam.targetTexture=rt;cam.Render();var previous=RenderTexture.active;RenderTexture.active=rt;var t=new Texture2D(size,size,alpha?TextureFormat.RGBA32:TextureFormat.RGB24,false);t.ReadPixels(new Rect(0,0,size,size),0,0);t.Apply();RenderTexture.active=previous;cam.targetTexture=null;rt.Release();UnityEngine.Object.Destroy(rt);return t;}
}
public class ForestWeaponReviewRunner:MonoBehaviour {}
