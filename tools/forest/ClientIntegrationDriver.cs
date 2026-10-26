using System;using System.IO;using System.Text;using UnityEngine;
// Disposable local test API. Installed only in ForestIntegrationClient, never shipped.
public class ClientIntegrationDriver:IModApi {
 static string folder;static float next;static bool busy;
 public void InitMod(Mod mod){Application.runInBackground=true;folder=Path.GetFullPath(Path.Combine(mod.Path,"../.."));ModEvents.UnityUpdate.RegisterHandler(Update);}
 static void Update(ref ModEvents.SUnityUpdateData data){
  if(GameManager.IsDedicatedServer||Time.realtimeSinceStartup<40||Time.realtimeSinceStartup<next||busy)return;next=Time.realtimeSinceStartup+1;string path=Path.Combine(folder,"client-command.txt");if(!File.Exists(path))return;
  string command=File.ReadAllText(path).Trim();File.Move(path,path+".processed-"+DateTime.UtcNow.Ticks);busy=true;
  try{
   if(command=="startlocal"){
    if(GameManager.Instance.World!=null)throw new Exception("World already running");
    if(!File.Exists(Path.Combine(folder,"allow-local-fixture.txt")))throw new Exception("Local fixture marker required");
    GamePrefs.Set(EnumGamePrefs.GameWorld,"Allium-v0.10");GamePrefs.Set(EnumGamePrefs.GameName,"ForestTest01");
    GamePrefs.Instance.Load(GameIO.GetSaveGameDir()+"/gameOptions.sdf");
    ConnectionManager.Instance.StartServers(GamePrefs.GetString(EnumGamePrefs.GameMode),false);
    Write("Started disposable local save");
   }else if(command=="connect"||command=="connectsave"){
    if(GameManager.Instance.World!=null)throw new Exception("Refusing to replace an active client world");
    var server=new GameServerInfo();server.SetValue(GameInfoString.IP,"127.0.0.1");server.SetValue(GameInfoInt.Port,command=="connectsave"?27980:27930);ServerInfoCache.Instance.SavePassword(server,"delve-local-test");GameManager.Instance.showOpenerMovieOnLoad=false;ConnectionManager.Instance.LastJoinSource="Isolated integration fixture";ConnectionManager.Instance.Connect(server);
    Write("REQUESTED native connection to isolated localhost server");
   }else if(command=="spawn"){
    var world=GameManager.Instance.World;if(world==null||!world.IsRemote()||!ConnectionManager.Instance.IsConnected||world.GetPrimaryPlayer()!=null)throw new Exception("Spawn requires a connected test world without a player");
    XUiC_SpawnSelectionWindow.GetWindow(LocalPlayerUI.primaryUI).SpawnButtonPressed((SpawnMethod)0,-1);Write("REQUESTED native spawn through selection-window handler");
   }else if(command=="fixture"){
    if(GameManager.Instance.World==null||GameManager.Instance.World.GetPrimaryPlayer()==null)throw new Exception("Fixture requires a loaded local player");
    var assembly=System.Reflection.Assembly.Load(File.ReadAllBytes(Path.Combine(folder,"ClientFixture.dll")));Write((string)assembly.GetType("ClientFixture").GetMethod("Run").Invoke(null,null));
   }else if(command=="inspect"){
    var world=GameManager.Instance.World;var p=world==null?null:world.GetPrimaryPlayer();var s=new StringBuilder();s.AppendLine("remoteWorld="+(world!=null&&world.IsRemote())+" connected="+ConnectionManager.Instance.IsConnected);
    if(p!=null){s.AppendLine("player="+p.entityId+" type="+p.GetType().Name+" position="+p.position+" health="+p.Health);s.AppendLine("held="+p.inventory.holdingItemItemValue.ItemClass.GetItemName());s.AppendLine("nativeUI="+(p.PlayerUI!=null));s.AppendLine("loadedEntities="+world.EntityAlives.Count);}
    Write(s.ToString());
   }else if(command=="disconnect"){
    ConnectionManager.Instance.DisconnectFromServer();Write("REQUESTED native disconnect");
   }else throw new Exception("Unsupported isolated test command");
  }catch(Exception ex){Write("FAIL "+ex);}finally{busy=false;}
 }
 static void Write(string text){File.WriteAllText(Path.Combine(folder,"client-result.txt"),DateTime.UtcNow.ToString("o")+"\n"+text);Log.Out("[ClientIntegration] "+text);}
}


