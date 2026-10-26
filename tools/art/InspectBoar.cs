using System;
using System.IO;
using System.Text;
using UnityEngine;
public class InspectBoar : IModApi {
 static string path; static bool done;
 public void InitMod(Mod m) { path=m.Path; ModEvents.UnityUpdate.RegisterHandler(Tick); }
 static void Tick(ref ModEvents.SUnityUpdateData d) {
  if(done || Time.realtimeSinceStartup<35)return; done=true;
  try {
   var p=DataLoader.LoadAsset<GameObject>("@:Entities/Animals/Boar/animalBoarPrefab.prefab",true);
   var o=UnityEngine.Object.Instantiate(p); var s=new StringBuilder();
   foreach(var t in o.GetComponentsInChildren<Transform>(true)) {
    s.AppendLine("NODE "+t.name+" parent="+(t.parent==null?"-":t.parent.name)+" pos="+t.localPosition.ToString("F4")+" rot="+t.localRotation.ToString("F4")+" scale="+t.localScale.ToString("F4"));
   }
   foreach(var r in o.GetComponentsInChildren<SkinnedMeshRenderer>(true))s.AppendLine("SKIN "+r.name+" bounds="+r.bounds+" root="+(r.rootBone==null?"-":r.rootBone.name)+" bones="+r.bones.Length);
   foreach(var a in o.GetComponentsInChildren<Animator>(true)) {
    s.AppendLine("ANIMATOR "+a.name+" rootmotion="+a.applyRootMotion);
    foreach(var v in a.parameters)s.AppendLine("PARAM "+v.name+" "+v.type);
    foreach(var c in a.runtimeAnimatorController.animationClips)s.AppendLine("CLIP "+c.name+" length="+c.length);
   }
   File.WriteAllText(Path.Combine(path,"../../native-boar.txt"),s.ToString());
  }catch(Exception ex){File.WriteAllText(Path.Combine(path,"../../native-boar.txt"),ex.ToString());}
  Application.Quit();
 }
}
