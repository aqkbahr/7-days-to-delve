using System;
using System.IO;
using System.Text;
using UnityEngine;
public class InspectEnemyRigs : IModApi {
 static string path; static bool done;
 public void InitMod(Mod m) { path=m.Path; ModEvents.UnityUpdate.RegisterHandler(Tick); }
 static void Tick(ref ModEvents.SUnityUpdateData d) {
  if(done || Time.realtimeSinceStartup<35)return; done=true;
  try {
   string[] ids={"delveCorruptedWalker","delveImp","delvePossessedSoldier","delveDemonSpawn","delveWarpedBrute","delveAshboundWarden"}; string[] paths={"@:Entities/Zombies/Boe/ZBoe.prefab","@:Entities/Zombies/Spider/ZSpider.prefab","@:Entities/Zombies/Soldier/ZSoldier.prefab","@:Entities/Zombies/Joe/ZJoe.prefab","@:Entities/Zombies/Hawaiian/ZHawaiian.prefab","@:Entities/Zombies/Biker/ZBiker.prefab"}; for(int i=0;i<ids.Length;i++){var p=DataLoader.LoadAsset<GameObject>(paths[i],true);
   var o=UnityEngine.Object.Instantiate(p); var s=new StringBuilder();
   foreach(var t in o.GetComponentsInChildren<Transform>(true)) {
    s.AppendLine("NODE "+t.name+" parent="+(t.parent==null?"-":t.parent.name)+" pos="+t.localPosition.ToString("F6")+" rot="+t.localRotation.ToString("F6")+" scale="+t.localScale.ToString("F6"));
   }
   foreach(var r in o.GetComponentsInChildren<SkinnedMeshRenderer>(true))s.AppendLine("SKIN "+r.name+" bounds="+r.bounds+" root="+(r.rootBone==null?"-":r.rootBone.name)+" bones="+r.bones.Length);
   foreach(var a in o.GetComponentsInChildren<Animator>(true)) {
    s.AppendLine("ANIMATOR "+a.name+" rootmotion="+a.applyRootMotion);
    foreach(var v in a.parameters)s.AppendLine("PARAM "+v.name+" "+v.type);
    if(a.runtimeAnimatorController!=null)foreach(var c in a.runtimeAnimatorController.animationClips)s.AppendLine("CLIP "+c.name+" length="+c.length);
   }
   File.WriteAllText(Path.Combine(path,"../../"+ids[i]+"-rig.txt"),s.ToString());UnityEngine.Object.Destroy(o); }
  }catch(Exception ex){File.WriteAllText(Path.Combine(path,"../../inspection-error.txt"),ex.ToString());}
  Application.Quit();
 }
}


