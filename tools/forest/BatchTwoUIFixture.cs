using System;using System.IO;using System.Text;using System.Collections;using System.Collections.Generic;using System.Reflection;using UnityEngine;
public class BatchTwoUIFixture:MonoBehaviour {
 EntityPlayerLocal p;string folder;StringBuilder report=new StringBuilder();
 void Capture(string n){Type.GetType("UnityEngine.ScreenCapture, UnityEngine.ScreenCaptureModule").GetMethod("CaptureScreenshot",new[]{typeof(string),typeof(int)}).Invoke(null,new object[]{Path.Combine(folder,n+".png"),1});}
 IEnumerator Start(){p=GameManager.Instance.World.GetPrimaryPlayer();folder=GameIO.GetUserGameDataDir();var run=Run();while(true){bool more;object current=null;try{more=run.MoveNext();if(more)current=run.Current;}catch(Exception ex){File.WriteAllText(Path.Combine(folder,"batch02-ui.txt"),report+"FAIL "+ex);yield break;}if(!more)break;yield return current;}File.WriteAllText(Path.Combine(folder,"batch02-ui.txt"),report+"PASS UI fixture completed");Destroy(gameObject);}
 void Check(bool ok,string text){if(!ok)throw new Exception(text);report.AppendLine("PASS "+text);}
 IEnumerator Run(){
  p.PlayerUI.windowManager.Close("spawnselection");LocalPlayerUI.primaryUI.windowManager.Close("spawnselection");p.PlayerUI.windowManager.ReEnableHUD();yield return new WaitForSeconds(.5f);
  p.IsGodMode.Value=true;var world=GameManager.Instance.World;var pos=p.GetBlockPosition()+new Vector3i(2,0,2);pos.y=world.GetHeight(pos.x,pos.z)+1;
  var spawn=Block.GetBlockValue("delveWayrestStewardSpawn",false);spawn.rotation=2;world.SetBlocksRPC(new List<BlockChangeInfo>{new BlockChangeInfo(new BlockValueRef(pos),spawn)});
  yield return new WaitForSeconds(5);
  EntityNPC npc=null;foreach(var e in world.EntityAlives)if(e is EntityNPC && EntityClass.GetEntityClassName(e.entityClass)=="delveWayrestSteward"){npc=(EntityNPC)e;break;}
  if(npc==null){npc=EntityFactory.CreateEntity(EntityClass.FromString("delveWayrestSteward"),p.position+new Vector3(0,0,3)) as EntityNPC;npc.world=world;world.SpawnEntityInWorld(npc);report.AppendLine("LIMIT: local NPC fixture; saved-world server interaction still required");}
  Check(npc!=null,"Steward fixture available");
  p.PlayerUI.xui.Dialog.Respondent=npc;p.PlayerUI.windowManager.Open("dialog",true);yield return new WaitForSeconds(1);
  var group=p.PlayerUI.xui.Dialog.DialogWindowGroup;Check(group!=null,"native dialog window opens");
  var list=group.GetChildByType<XUiC_DialogResponseList>();
  foreach(string id in new[]{"wayrestWelcome","wayrestIncursions","wayrestRefuge","delveTraining"}){
   var response=group.CurrentDialog.GetResponse(id);Check(response!=null,id+" response exists");
   var entry=list.GetChildByType<XUiC_DialogResponseEntry>();entry.CurrentResponse=response;entry.HasRequirement=true;
   typeof(XUiC_DialogResponseList).GetMethod("OnPressResponse",BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public).Invoke(list,new object[]{entry,0});yield return new WaitForSeconds(.5f);
   var reply=p.PlayerUI.xui.GetWindowByType<Delve.XUiC_StewardReply>();Check(reply!=null,"reply panel exists");string value="";reply.GetBindingValueInternal(ref value,"delve_reply");Check(value==group.CurrentDialog.CurrentStatement.Text&&value.Length>40,id+" displayed binding matches complete statement");report.AppendLine("PANEL visible="+reply.ViewComponent.IsVisible+" active="+reply.ViewComponent.UiTransform.gameObject.activeInHierarchy+" pos="+reply.ViewComponent.UiTransform.position+" HUD="+p.PlayerUI.windowManager.IsHUDEnabled());Capture("batch02-dialog-"+id);yield return new WaitForSeconds(.3f);
   entry.CurrentResponse=group.CurrentDialog.GetResponse("nevermind");entry.HasRequirement=true;typeof(XUiC_DialogResponseList).GetMethod("OnPressResponse",BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public).Invoke(list,new object[]{entry,0});yield return new WaitForSeconds(.3f);Check(group.CurrentDialog.CurrentStatement.ID=="start","back returns to main choices");
  }
  var roster=list.GetChildByType<XUiC_DialogResponseEntry>();roster.CurrentResponse=group.CurrentDialog.GetResponse("wayrestOpenRoster");roster.HasRequirement=true;typeof(XUiC_DialogResponseList).GetMethod("OnPressResponse",BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public).Invoke(list,new object[]{roster,0});yield return new WaitForSeconds(2);
  Check(p.PlayerUI.windowManager.IsWindowOpen("delveRecruits"),"Steward choice opens settlement roster");Capture("batch02-roster");yield return new WaitForSeconds(.3f);p.PlayerUI.windowManager.Close("delveRecruits");
  p.SetFirstPersonView(true,false);p.inventory.SetItem(0,ItemClass.GetItem("delveBoneDagger",false),1);p.inventory.SetHoldingItemIdxNoHolsterTime(0);yield return new WaitForSeconds(1);Capture("batch02-dagger");yield return new WaitForSeconds(.3f);
  var plate=Block.GetBlockValue("delveFarmPlotPlate",false);for(byte rot=0;rot<24;rot++){plate.rotation=rot;var boxes=plate.Block.shape.GetBounds(plate);if(boxes!=null&&boxes.Length>0&&boxes[0].size.y<.3f)report.AppendLine("PLATE "+rot+" "+boxes[0]);}
 }
}
