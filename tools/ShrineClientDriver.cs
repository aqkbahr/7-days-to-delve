using System;using System.IO;using System.Linq;using System.Text;using UnityEngine;using Delve;
// Disposable localhost client driver, never included in a release.
public class ShrineClientDriver:IModApi {
 static string folder;static float next;static string replay;static int death;static string rid,sid;static Vector3i pos,replayPos;
 public void InitMod(Mod mod){Application.runInBackground=true;folder=Path.GetFullPath(Path.Combine(mod.Path,"../.."));ModEvents.UnityUpdate.RegisterHandler(Update);}
 static void Update(ref ModEvents.SUnityUpdateData data){
  if(GameManager.IsDedicatedServer||Time.realtimeSinceStartup<40||Time.realtimeSinceStartup<next)return;next=Time.realtimeSinceStartup+1;
  string path=Path.Combine(folder,"client-command.txt");if(!File.Exists(path))return;string cmd=File.ReadAllText(path).Trim();File.Move(path,path+".processed-"+DateTime.UtcNow.Ticks);
  try{
   var w=GameManager.Instance.World;var p=w==null?null:w.GetPrimaryPlayer();
   if(cmd=="connect") {if(w!=null)throw new Exception("Refusing active world replacement");var s=new GameServerInfo();s.SetValue(GameInfoString.IP,"127.0.0.1");s.SetValue(GameInfoInt.Port,28290);ServerInfoCache.Instance.SavePassword(s,"delve-local-test");GameManager.Instance.showOpenerMovieOnLoad=false;ConnectionManager.Instance.LastJoinSource="Shrine acceptance";ConnectionManager.Instance.Connect(s);Write("Connection requested");return;}
   if(cmd=="spawn"){if(w==null||!w.IsRemote()||p!=null)throw new Exception("Expected connected world before spawn");GameManager.Instance.RequestToSpawn(-1);Write("Spawn requested");return;}
   if(cmd=="disconnect"){ConnectionManager.Instance.DisconnectFromServer();Write("Disconnected");return;}
   if(cmd=="quit"){Write("Quitting isolated client");Application.Quit();return;}
   if(cmd=="status"){Write("world="+(w!=null)+" connected="+ConnectionManager.Instance.IsConnected+" player="+(p!=null));return;}
   if(p==null)throw new Exception("No local player");
   if(cmd.StartsWith("press ")){var ui=p.PlayerUI.xui.GetWindowByType<XUiC_RecruitScreen>();var b=(XUiC_SimpleButton)ui.GetChildById(cmd.Substring(6));typeof(XUiC_SimpleButton).GetMethod("Btn_OnPress",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Public).Invoke(b,new object[]{b,0});Write("Invoked native button event "+cmd);return;}
   if(cmd=="tick"){p.PlayerUI.xui.GetWindowByType<XUiC_RecruitScreen>().Update(5.1f);Write("Advanced hidden native menu update by 5.1 seconds");return;}
   if(cmd=="menu") {var ui=p.PlayerUI.xui.GetWindowByType<XUiC_RecruitScreen>();var report=new StringBuilder();report.AppendLine("windowOpen="+p.PlayerUI.windowManager.IsWindowOpen("delveRecruits")+" controllerOpened="+typeof(XUiC_RecruitScreen).GetField("opened",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic).GetValue(ui));foreach(var key in new[]{"nr_atshrine","nr_detail","nr_message","nr_row0","nr_row1"}){string value="";ui.GetBindingValueInternal(ref value,key);report.AppendLine(key+"="+value);}Write(report.ToString());return;}
   if(cmd=="capture"){var t=Type.GetType("UnityEngine.ScreenCapture, UnityEngine.ScreenCaptureModule");t.GetMethod("CaptureScreenshot",new[]{typeof(string),typeof(int)}).Invoke(null,new object[]{Path.Combine(folder,"shrine-menu.png"),1});Write("Requested native rendered frame capture");return;}
   if(cmd.StartsWith("open ")){var a=cmd.Split(' ');pos=new Vector3i(int.Parse(a[1]),int.Parse(a[2]),int.Parse(a[3]));if(a.Length>4)w.GetBlock(pos).Block.OnBlockActivated(a[4],w,pos,w.GetBlock(pos),p);else w.GetBlock(pos).Block.OnBlockActivated(w,pos,w.GetBlock(pos),p);Write("Native block activation requested at "+pos);return;}
   if(cmd=="close"){p.PlayerUI.windowManager.Close("delveRecruits");Write("Closed");return;}
   if(cmd=="burst"||cmd=="replay"||cmd=="spoof"||cmd=="stale"){
    if(cmd!="replay"){var r=RecruitScreen.View.Recruits.First(x=>x.Id==RecruitScreen.Selected);rid=r.Id;sid=RecruitScreen.Settlement;death=r.Deaths-(cmd=="stale"?1:0);replayPos=RecruitScreen.Position;replay=Guid.NewGuid().ToString("N");}
    for(int i=0;i<(cmd=="burst"?12:1);i++)ConnectionManager.Instance.SendToServer(NetPackageManager.GetPackage<NetPackageDelveRecruitRequest>().Setup(cmd=="spoof"?p.entityId+999:p.entityId,"resurrect",sid,rid,replayPos,-1,replay,death),false);
    Write("Sent "+cmd+" via native network; generation="+death);return;
   }
   if(cmd=="refresh"){RecruitScreen.Send(p,"view");Write("Refresh requested");return;}
   if(cmd=="inspect"){
    var b=new StringBuilder();b.AppendLine("remote="+w.IsRemote()+" connected="+ConnectionManager.Instance.IsConnected+" player="+p.entityId+" position="+p.position+" health="+p.Health);b.AppendLine("waiting="+RecruitScreen.Waiting+" shrine="+RecruitScreen.View.AtShrine+" selected="+RecruitScreen.Selected+" message="+RecruitScreen.View.Message);
    foreach(var r in RecruitScreen.View.Recruits)b.AppendLine("RECRUIT "+r.Id+" name="+r.Name+" role="+r.Role+" tier="+r.Tier+" state="+r.Status+" deaths="+r.Deaths+" ready="+r.RecoveryReadyAt);
    b.AppendLine("livingRecruitBodies="+w.EntityAlives.Count(x=>x is EntityDelveRecruit&&!x.IsDead()));Write(b.ToString());return;
   }
   throw new Exception("Unknown command");
  }catch(Exception ex){Write("FAIL "+ex);}
 }
 static void Write(string s){File.WriteAllText(Path.Combine(folder,"client-result.txt"),DateTime.UtcNow.ToString("o")+"\n"+s);File.AppendAllText(Path.Combine(folder,"acceptance-history.txt"),DateTime.UtcNow.ToString("o")+"\n"+s+"\n");Log.Out("[ShrineClient] "+s);}
}
