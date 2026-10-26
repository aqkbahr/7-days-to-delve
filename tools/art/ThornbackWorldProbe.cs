using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using UnityEngine;
using DelveThornback;
using DelveForest;

public class ConsoleCmdThornbackProbe:ConsoleCmdAbstract {
 static ChunkManager.ChunkObserver observer;
 public override string[] getCommands(){return new[]{"thornbackprobe"};}
 public override string getDescription(){return "Isolated Thornback fixture: load | run";}
 public override void Execute(List<string> args,CommandSenderInfo sender){
  try {
   var world=GameManager.Instance.World;if(world==null)throw new Exception("World not ready");
   if(args.Count==0)throw new Exception(getDescription());
   if(args[0]=="load"){if(observer!=null)GameManager.Instance.RemoveChunkObserver(observer);observer=GameManager.Instance.AddChunkObserver(new Vector3(0,80,0),false,4,3);SdtdConsole.Instance.Output("[ThornbackWorld] Loading fixture terrain at 0,0");}
   else if(args[0]=="run"){new GameObject("ThornbackWorldRunner").AddComponent<ThornbackWorldRunner>();SdtdConsole.Instance.Output("[ThornbackWorld] Test started; read world-result.txt");}
  }catch(Exception e){SdtdConsole.Instance.Output("[ThornbackWorld] FAIL "+e);}
 }
}
public class ThornbackWorldRunner:MonoBehaviour {
 EntityAlive boar,control;EntityPlayer target;World world;ThornbackVisual art;string output;GameObject fixtureFloor;float floorHeight;
 StringBuilder report=new StringBuilder();
 void FixedUpdate(){if(fixtureFloor==null)return;fixtureFloor.layer=31;foreach(var entity in new EntityAlive[]{boar,control})if(entity!=null)foreach(var c in entity.GetComponentsInChildren<Collider>(true)){Physics.IgnoreLayerCollision(31,c.gameObject.layer,false);Physics.IgnoreCollision(fixtureFloor.GetComponent<Collider>(),c,false);}}
 void Check(bool condition,string text){if(!condition)throw new Exception(text);report.AppendLine("PASS "+text);}
 IEnumerator Start(){
  output=Path.Combine(GameIO.GetSaveGameDir(),"ThornbackArtEvidence");Directory.CreateDirectory(output);
  var run=Run();
  while(true){bool more=false;object current=null;try{more=run.MoveNext();if(more)current=run.Current;}catch(Exception e){File.WriteAllText(Path.Combine(output,"world-result.txt"),"FAIL\n"+report+e);Log.Error("[ThornbackWorld] "+e);Cleanup();yield break;}if(!more)break;yield return current;}
  File.WriteAllText(Path.Combine(output,"world-result.txt"),"PASS\n"+report);Log.Out("[ThornbackWorld] PASS; evidence="+output);Cleanup();
 }
 IEnumerator Run(){
  world=GameManager.Instance.World;
  foreach(var player in world.GetPlayers())throw new Exception("Fixture requires no connected players");
  float height=world.GetHeight(0,0);Check(height>0,"Terrain loaded at height "+height);
  var position=new Vector3(0,height+1,0);
  floorHeight=height;
  fixtureFloor=new GameObject("DisposableThornbackCollisionFloor");
  fixtureFloor.transform.position=new Vector3(0,height-.5f,0);
  var floor=fixtureFloor.AddComponent<BoxCollider>();floor.size=new Vector3(20,1,20);
  boar=EntityFactory.CreateEntity(EntityClass.FromString("delveThornbackBoar"),position) as EntityAlive;
  Check(boar!=null,"Native entity factory creates existing Thornback ID");world.SpawnEntityInWorld(boar);
  yield return new WaitForSeconds(2);
  art=boar.GetComponent<ThornbackVisual>();Check(art!=null && art.Ready,"Custom model attached to live world entity");art.ForceVisibleForProbe=true;
  Check(boar.emodel.avatarController is AvatarAnimalController,"Native animal controller retained");
  Check(boar.RootMotion,"Native root motion retained");Check(boar.emodel.HasRagdoll(),"Native ragdoll retained");
  Check(boar.GetComponentsInChildren<Collider>().Length>0,"Native entity colliders retained");
  int floorLayer=-1;
  for(int layer=0;layer<30;layer++){bool collides=true;foreach(var collider in boar.GetComponentsInChildren<Collider>())if(!collider.isTrigger && Physics.GetIgnoreLayerCollision(layer,collider.gameObject.layer))collides=false;if(collides){floorLayer=layer;break;}}
  Check(floorLayer>=0,"Controlled floor uses existing compatible collision layer "+floorLayer);
  fixtureFloor.layer=floorLayer;Physics.SyncTransforms();
  Check(boar.GetMaxHealth()>=208 && boar.GetMaxHealth()<=299,"Thornback HP within native animal scaling range: "+boar.GetMaxHealth());
  Check(Mathf.Abs(EffectManager.GetValue(PassiveEffects.PhysicalDamageResist,null,0,boar)-20)<.01f,"Armor 20 unchanged");
  var hand=ItemClass.GetItem("delveThornbackBoarAttack",false);float damage=EffectManager.GetValue(PassiveEffects.EntityDamage,hand,0,boar);
  Check(Mathf.Abs(damage-16)<.01f,"Base attack damage 16 unchanged");
  Check(boar.EntityClass.Properties.GetString("HandItem")=="delveThornbackBoarAttack","Attack item identity preserved");
  var harvest=boar.EntityClass.itemsToDrop[EnumDropEvent.Harvest];
  Check(harvest.Exists(drop=>drop.name=="delveThornhide" && drop.minCount==2 && drop.maxCount==2),"Two Thornhide harvest definition retained");
  report.AppendLine("INFO Existing bestiary harvest list: "+String.Join(",",harvest.ConvertAll(drop=>drop.name+":"+drop.minCount+"-"+drop.maxCount).ToArray()));
  Capture("world-idle.png");
  target=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),position+new Vector3(3,0,0)) as EntityPlayer;target.world=world;
  boar.SetAttackTarget(target,120);yield return new WaitForSeconds(1.3f);
  var cycle=boar.GetComponent<HeavyAttackCycle>();Check(cycle!=null,"Native Forest heavy attack cycle retained");
  var next=typeof(HeavyAttackCycle).GetField("next",BindingFlags.NonPublic|BindingFlags.Instance);
  var phase=typeof(HeavyAttackCycle).GetField("phase",BindingFlags.NonPublic|BindingFlags.Instance);
  var tick=typeof(HeavyAttackCycle).GetMethod("Update",BindingFlags.NonPublic|BindingFlags.Instance);
  string[] buffs={"delveForestBrace","delveForestRush","delveForestSpent"};string[] states={"Brace","Rush","Recovery"};
  for(int i=0;i<3;i++){
   phase.SetValue(cycle,i);next.SetValue(cycle,0f);tick.Invoke(cycle,null);next.SetValue(cycle,Time.time+60);boar.Buffs.Tick();
   yield return new WaitForSeconds(i==2?.8f:.25f);
   Check(boar.Buffs.HasBuff(buffs[i]),"Server phase buff "+buffs[i]);
   Check(art.State==states[i],"Art follows server phase "+states[i]+" (actual "+art.State+")");
   float expected=damage*(i==1?1.25f:.5f);Check(Mathf.Abs(EffectManager.GetValue(PassiveEffects.EntityDamage,hand,0,boar)-expected)<.01f,"Native phase damage unchanged: "+expected);
   Capture("world-"+states[i].ToLowerInvariant()+".png");
  }
  foreach(string buff in buffs)boar.Buffs.RemoveBuff(buff);next.SetValue(cycle,Time.time+60);
  boar.emodel.avatarController.StartAnimationAttack();yield return new WaitForSeconds(.1f);
  Check(art.State=="Attack" || art.State=="AttackRunning","Custom attack follows native attack state: "+art.State);
  Capture("world-attack.png");yield return new WaitForSeconds(.6f);
  // Deliberately use the native damage pipeline, not a custom animation event.
  int before=boar.Health;boar.DamageEntity(new DamageSource(EnumDamageSource.External,EnumDamageTypes.Bashing),20,false,1);yield return new WaitForSeconds(.15f);
  Check(boar.Health<before,"Native damage is received");
  Capture("world-hit.png");
  control=EntityFactory.CreateEntity(EntityClass.FromString("animalBoar"),position+new Vector3(3,0,0)) as EntityAlive;world.SpawnEntityInWorld(control);yield return new WaitForSeconds(.5f);
  control.DamageEntity(new DamageSource(EnumDamageSource.External,EnumDamageTypes.Bashing),10000,false,1);
  boar.DamageEntity(new DamageSource(EnumDamageSource.External,EnumDamageTypes.Bashing),10000,false,1);
  foreach(var c in boar.GetComponentsInChildren<Collider>(true))report.AppendLine("INFO deathCollider "+c.name+" layer="+c.gameObject.layer+" enabled="+c.enabled+" active="+c.gameObject.activeInHierarchy+" trigger="+c.isTrigger+" floorIgnored="+Physics.GetIgnoreLayerCollision(fixtureFloor.layer,c.gameObject.layer));
  foreach(var rb in boar.GetComponentsInChildren<Rigidbody>(true))report.AppendLine("INFO deathBody "+rb.name+" pos="+rb.position+" kinematic="+rb.isKinematic+" detect="+rb.detectCollisions);
  for(int layer=0;layer<30;layer++){bool ok=true;foreach(var c in boar.GetComponentsInChildren<Collider>())if(c.enabled && !c.isTrigger && Physics.GetIgnoreLayerCollision(layer,c.gameObject.layer))ok=false;if(ok){fixtureFloor.layer=layer;break;}}
  report.AppendLine("INFO Death floor layer="+fixtureFloor.layer);Physics.SyncTransforms();yield return new WaitForSeconds(1.5f);
  Check(boar.IsDead(),"Native lethal damage and corpse state");
  Check(art.Ready,"Custom skin survives death");
  Check(art.State=="Death" || art.State=="Corpse","Death/corpse visual state: "+art.State);
  foreach(var rb in boar.GetComponentsInChildren<Rigidbody>(true))report.AppendLine("INFO finalBody "+rb.name+" pos="+rb.position+" kinematic="+rb.isKinematic+" detect="+rb.detectCollisions);
  foreach(var rb in control.GetComponentsInChildren<Rigidbody>(true))report.AppendLine("INFO controlBody "+rb.name+" pos="+rb.position);
  report.AppendLine("INFO floor "+fixtureFloor.transform.position+" enabled="+fixtureFloor.GetComponent<Collider>().enabled);
  foreach(var c in boar.GetComponentsInChildren<Collider>(true))report.AppendLine("INFO finalCollider "+c.name+" layer="+c.gameObject.layer+" enabled="+c.enabled+" trigger="+c.isTrigger+" ignored="+Physics.GetIgnoreLayerCollision(fixtureFloor.layer,c.gameObject.layer));
  Capture("world-corpse.png");
  report.AppendLine("INFO RagdollActive="+boar.emodel.IsRagdollActive+"; entity="+boar.entityId);
  Check(EntityClass.GetEntityClassName(boar.entityClass)=="delveThornbackBoar","Corpse retains harvest entity identity");
  report.AppendLine("LIMIT Fixture verifies native entity/state/damage/render path on a controlled collision floor; not human terrain traversal, full combat balance or multiplayer. Captures render baked snapshots of the live skinned pose to avoid physics/GPU frame races.");
 }
 void Capture(string name){
  foreach(var t in art.Visual.GetComponentsInChildren<Transform>(true))t.gameObject.layer=30;
  art.Visual.GetComponent<LODGroup>().ForceLOD(0);
  foreach(var r in art.Visual.GetComponentsInChildren<Renderer>()){r.forceRenderingOff=false;r.enabled=r.name=="Thornback_LOD0";}
  var mainSkin=Array.Find(art.Visual.GetComponentsInChildren<SkinnedMeshRenderer>(),s=>s.name=="Thornback_LOD0");
  var baked=new Mesh();mainSkin.BakeMesh(baked);var vertices=baked.vertices;
  var actualBounds=new Bounds(mainSkin.transform.TransformPoint(vertices[0]),Vector3.zero);
  foreach(var vertex in vertices)actualBounds.Encapsulate(mainSkin.transform.TransformPoint(vertex));
  report.AppendLine("INFO "+name+" skinBounds="+actualBounds+" root="+art.Visual.transform.position);
  Check(actualBounds.size.magnitude>.4f && actualBounds.size.magnitude<6,"Sane skinned bounds for "+name);
  if(name=="world-corpse.png")Check(actualBounds.center.y>floorHeight-1,"Ragdoll remains on controlled collision floor");
  mainSkin.localBounds=baked.bounds;
  // A dedicated server advances physics independently of a player camera.
  // Render the current baked pose to prevent a one-frame GPU skinning lag.
  var snapshot=new GameObject("PosedSkinSnapshot");snapshot.layer=30;
  snapshot.transform.position=mainSkin.transform.position;snapshot.transform.rotation=mainSkin.transform.rotation;snapshot.transform.localScale=mainSkin.transform.lossyScale;
  snapshot.AddComponent<MeshFilter>().sharedMesh=baked;snapshot.AddComponent<MeshRenderer>().sharedMaterial=mainSkin.sharedMaterial;
  foreach(var r in art.Visual.GetComponentsInChildren<Renderer>())r.forceRenderingOff=true;
  var center=actualBounds.center;
  var go=new GameObject("WorldProbeCamera");var camera=go.AddComponent<Camera>();camera.enabled=false;camera.cullingMask=1<<30;camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.035f,.045f,.055f);camera.fieldOfView=35;camera.farClipPlane=30;
  camera.transform.position=center+new Vector3(1.7f,1,2.3f);camera.transform.LookAt(center);
  var lg=new GameObject("WorldProbeLight");var light=lg.AddComponent<Light>();light.type=LightType.Directional;light.intensity=1.1f;light.cullingMask=1<<30;lg.transform.rotation=Quaternion.Euler(35,-35,0);
  var oldAmbient=RenderSettings.ambientLight;var oldMode=RenderSettings.ambientMode;RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;RenderSettings.ambientLight=Color.gray;
  var rt=new RenderTexture(768,768,24);camera.targetTexture=rt;camera.Render();var previous=RenderTexture.active;RenderTexture.active=rt;var tex=new Texture2D(768,768,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,768,768),0,0);tex.Apply();RenderTexture.active=previous;
  File.WriteAllBytes(Path.Combine(output,name),tex.EncodeToPNG());
  int visiblePixels=0;foreach(var pixel in tex.GetPixels32())if(pixel.r>35 || pixel.g>35 || pixel.b>40)visiblePixels++;
  camera.targetTexture=null;rt.Release();Destroy(rt);Destroy(tex);Destroy(go);Destroy(lg);RenderSettings.ambientLight=oldAmbient;RenderSettings.ambientMode=oldMode;
  Destroy(snapshot);Destroy(baked);
  foreach(var r in art.Visual.GetComponentsInChildren<Renderer>())r.forceRenderingOff=false;
  Check(visiblePixels>1000,"Visible rendered model for "+name+" pixels="+visiblePixels);
 }
 void Cleanup(){if(control!=null && world!=null)world.RemoveEntity(control.entityId,EnumRemoveEntityReason.Despawned);if(boar!=null && world!=null)world.RemoveEntity(boar.entityId,EnumRemoveEntityReason.Despawned);if(target!=null)Destroy(target.gameObject);if(fixtureFloor!=null)Destroy(fixtureFloor);Destroy(gameObject);}
}



