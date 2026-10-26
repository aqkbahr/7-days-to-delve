using System;using System.Collections;using System.Collections.Generic;using System.IO;using System.Text;using UnityEngine;using DelvePresentation;
public class ConsoleCmdPresentationProbe:ConsoleCmdAbstract {
 public override string[] getCommands(){return new[]{"presentationverify"};}
 public override string getDescription(){return "Run isolated graphical native-controller fixtures with no connected players.";}
 public override void Execute(List<string> args,CommandSenderInfo sender){
  if(!GameManager.Instance.GameHasStarted){SdtdConsole.Instance.Output("[Presentation] Wait for completed game startup.");return;}
  if(GameManager.Instance.World==null||GameManager.Instance.World.GetPlayers().Count>0){SdtdConsole.Instance.Output("[Presentation] Requires an isolated world with no players.");return;}
  if(SystemInfo.graphicsDeviceType==UnityEngine.Rendering.GraphicsDeviceType.Null){SdtdConsole.Instance.Output("[Presentation] Requires graphics-enabled fixture server.");return;}
  new GameObject("PresentationFixture").AddComponent<PresentationFixture>();SdtdConsole.Instance.Output("[Presentation] Started; results in save/PresentationEvidence.");
 }
}
public class PresentationFixture:MonoBehaviour {
 StringBuilder report=new StringBuilder();EntityAlive entity;string output;int count;ChunkManager.ChunkObserver observer;float previousCampaignTick;bool campaignPaused;
 void Update(){if(entity!=null&&entity.emodel!=null)entity.emodel.SetVisible(true,true);}
 void Check(bool ok,string message){count++;if(!ok)throw new Exception(message);report.AppendLine("PASS "+message);}
 IEnumerator Start(){output=Path.Combine(GameIO.GetSaveGameDir(),"PresentationEvidence");Directory.CreateDirectory(output);var run=Run();while(true){bool more=false;object value=null;try{more=run.MoveNext();if(more)value=run.Current;}catch(Exception ex){File.WriteAllText(Path.Combine(output,"result.txt"),"FAIL\n"+report+ex);Cleanup();yield break;}if(!more)break;yield return value;}File.WriteAllText(Path.Combine(output,"result.txt"),"PASS "+count+" checks\n"+report+"\nLIMIT: scripted native pose, damage and corpse fixtures; not terrain traversal, human combat or multiplayer acceptance.");Cleanup();}
 IEnumerator Run(){
  var world=GameManager.Instance.World;
  var campaignTick=typeof(Delve.Core).GetField("nextTick",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static);previousCampaignTick=(float)campaignTick.GetValue(null);campaignTick.SetValue(null,float.MaxValue);campaignPaused=true;
  report.AppendLine("INFO Campaign polling paused only inside this empty-server mesh fixture; otherwise orphan Warden cleanup correctly removes a manually created boss. Campaign behavior has separate tests.");
  observer=GameManager.Instance.AddChunkObserver(new Vector3(0,80,0),false,4,3);
  float deadline=Time.realtimeSinceStartup+45;while(world.GetHeight(0,0)<=0&&Time.realtimeSinceStartup<deadline)yield return new WaitForSeconds(1);
  Check(world.GetHeight(0,0)>0,"fixture terrain loaded");
  foreach(var entry in EnemyRigs.Bundles){
   entity=EntityFactory.CreateEntity(EntityClass.FromString(entry.Key),new Vector3(0,world.GetHeight(0,0)+2,0)) as EntityAlive;Check(entity!=null,entry.Key+" factory");entity.world=world;entity.SetSpawnerSource(EnumSpawnerSource.StaticSpawner);world.SpawnEntityInWorld(entity);entity.emodel.SetVisible(true,true);
   yield return new WaitForSeconds(.5f);
   var art=entity.GetComponent<EnemyVisual>();Check(art!=null&&art.Visual!=null&&art.BonePairs>=25,entry.Key+" live native rig attachment");
   Check(entity.GetComponentsInChildren<Collider>(true).Length>0,entry.Key+" native colliders retained");Check(entity.emodel.avatarController!=null,entry.Key+" native controller retained");
   Check(entity.emodel.HasRagdoll(),entry.Key+" native ragdoll retained");Bounds before=Capture(art,entry.Key+"-idle");
   var idleVertices=Vertices(art);float displacement=0;
   entity.emodel.avatarController.StartAnimationAttack();
   for(int frame=0;frame<12;frame++){yield return new WaitForSeconds(.1f);var animated=Vertices(art);Check(animated.Length==idleVertices.Length,entry.Key+" stable animated topology");for(int v=0;v<animated.Length;v++)displacement=Math.Max(displacement,Vector3.Distance(animated[v],idleVertices[v]));}
   Check(displacement>.005f,entry.Key+" native attack deforms custom skin: "+displacement+"m");
   Check(entity!=null&&world.GetEntity(entity.entityId)!=null,entry.Key+" fixture entity retained by world");Check(art.Visual!=null,entry.Key+" attack visual retained; native model="+entity.emodel.modelTransform);Capture(art,entry.Key+"-attack");
   int health=entity.Health;entity.DamageEntity(new DamageSource(EnumDamageSource.External,EnumDamageTypes.Bashing),10,false,1);Check(entity.Health<health,entry.Key+" native health damage");
   entity.DamageEntity(new DamageSource(EnumDamageSource.External,EnumDamageTypes.Bashing),100000,false,1);yield return new WaitForSeconds(3);Check(entity.IsDead(),entry.Key+" native death");Check(art.Visual!=null,entry.Key+" custom skin survives death");Capture(art,entry.Key+"-corpse");
   world.RemoveEntity(entity.entityId,EnumRemoveEntityReason.Despawned);entity=null;yield return null;
  }
 }
 Vector3[] Vertices(EnemyVisual art){foreach(var skin in art.Visual.GetComponentsInChildren<SkinnedMeshRenderer>(true))if(skin.name.EndsWith("LOD0",StringComparison.Ordinal)){var mesh=new Mesh();skin.BakeMesh(mesh);var result=mesh.vertices;Destroy(mesh);return result;}throw new Exception("Missing primary skin for motion test");}
 Bounds Capture(EnemyVisual art,string name){
  var skins=art.Visual.GetComponentsInChildren<SkinnedMeshRenderer>(true);SkinnedMeshRenderer skin=null;foreach(var s in skins)if(s.name.EndsWith("LOD0",StringComparison.Ordinal)){skin=s;break;}Check(skin!=null,name+" primary skin");
  var mesh=new Mesh();skin.BakeMesh(mesh);var vertices=mesh.vertices;Check(vertices.Length>0,name+" vertices");var bounds=new Bounds(skin.transform.TransformPoint(vertices[0]),Vector3.zero);foreach(var v in vertices){CheckFinite(v,name);bounds.Encapsulate(skin.transform.TransformPoint(v));}Check(bounds.size.magnitude>.3f&&bounds.size.magnitude<9,name+" sane deformation "+bounds.size);
  var snapshot=new GameObject("Snapshot");snapshot.layer=30;snapshot.transform.position=skin.transform.position;snapshot.transform.rotation=skin.transform.rotation;snapshot.transform.localScale=skin.transform.lossyScale;snapshot.AddComponent<MeshFilter>().sharedMesh=mesh;snapshot.AddComponent<MeshRenderer>().sharedMaterial=skin.sharedMaterial;
  var camObject=new GameObject("FixtureCamera");var cam=camObject.AddComponent<Camera>();cam.enabled=false;cam.cullingMask=1<<30;cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.03f,.04f,.05f);cam.orthographic=true;cam.orthographicSize=Math.Max(.6f,bounds.size.magnitude*.6f);cam.farClipPlane=40;cam.transform.position=bounds.center+new Vector3(3,1.5f,5);cam.transform.LookAt(bounds.center);
  var lamp=new GameObject("FixtureLight");var light=lamp.AddComponent<Light>();light.type=LightType.Directional;light.intensity=1.2f;light.cullingMask=1<<30;lamp.transform.rotation=Quaternion.Euler(30,-30,0);
  var rt=new RenderTexture(512,512,24);cam.targetTexture=rt;cam.Render();var previous=RenderTexture.active;RenderTexture.active=rt;var image=new Texture2D(512,512,TextureFormat.RGB24,false);image.ReadPixels(new Rect(0,0,512,512),0,0);image.Apply();RenderTexture.active=previous;File.WriteAllBytes(Path.Combine(output,name+".png"),image.EncodeToPNG());int pixels=0;foreach(var p in image.GetPixels32())if(p.r>35||p.g>35||p.b>40)pixels++;Check(pixels>500,name+" visible rendered pixels "+pixels);
  cam.targetTexture=null;rt.Release();Destroy(rt);Destroy(image);Destroy(lamp);Destroy(camObject);Destroy(snapshot);Destroy(mesh);return bounds;
 }
 void CheckFinite(Vector3 v,string name){if(float.IsNaN(v.x)||float.IsNaN(v.y)||float.IsNaN(v.z)||float.IsInfinity(v.sqrMagnitude))throw new Exception(name+" non-finite skin");}
 void Cleanup(){if(entity!=null)GameManager.Instance.World.RemoveEntity(entity.entityId,EnumRemoveEntityReason.Despawned);if(observer!=null)GameManager.Instance.RemoveChunkObserver(observer);if(campaignPaused)typeof(Delve.Core).GetField("nextTick",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).SetValue(null,previousCampaignTick);Destroy(gameObject);}
}

