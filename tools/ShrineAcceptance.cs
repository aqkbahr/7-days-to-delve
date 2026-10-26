using System;using System.Linq;using System.Collections.Generic;using UnityEngine;using Delve;
// Explicitly disposable world only. Leaves the stage available for rendered UI checks.
public class ConsoleCmdShrineAcceptance:ConsoleCmdAbstract {
 static Vector3i claim,shrine,forge;static string id;static int playerId;
 public override string[] getCommands(){return new[]{"shrineaccept"};}
 public override string getDescription(){return "Isolated connected shrine acceptance fixture";}
 static void Check(bool ok,string msg){if(!ok)throw new Exception(msg);SdtdConsole.Instance.Output("[ShrineAcceptance] PASS "+msg);}
 public override void Execute(List<string> args,CommandSenderInfo sender){try{
  var w=GameManager.Instance.World;if(!GameIO.GetUserGameDataDir().Contains("WayrestRecruits"))throw new Exception("Wrong isolated profile");
  if(args[0]=="setup"){
   var p=w.GetPlayers().First();playerId=p.entityId;var pp=GameManager.Instance.persistentPlayers;var pd=pp.GetPlayerDataFromEntityID(p.entityId);
   Check(Core.Progress.Roster.Recruits.Count==0,"empty isolated roster before setup");
   claim=new Vector3i(2,w.GetHeightAt(2,2)+2,2);shrine=claim+new Vector3i(4,0,3);forge=claim+new Vector3i(4,0,0);var ledger=claim+new Vector3i(2,0,0);
   var changes=new List<BlockChangeInfo>();for(int x=0;x<=10;x++)for(int z=0;z<=10;z++)for(int y=claim.y-1;y<=claim.y+3;y++)changes.Add(new BlockChangeInfo(new BlockValueRef(new Vector3i(x,y,z)),y==claim.y-1?Block.GetBlockValue("woodLogPillar100",false):BlockValue.Air));w.SetBlocksRPC(changes);
   foreach(var pair in new[]{new KeyValuePair<Vector3i,string>(claim,"keystoneBlock"),new KeyValuePair<Vector3i,string>(ledger,"delveRecruitLedger"),new KeyValuePair<Vector3i,string>(forge,"delveForgeAnvil"),new KeyValuePair<Vector3i,string>(shrine,"delveRecoveryShrine")}){var b=Block.GetBlockValue(pair.Value,false);w.SetBlocksRPC(new List<BlockChangeInfo>{new BlockChangeInfo(new BlockValueRef(pair.Key),b)});var tile=w.GetTileEntity(pair.Key) as TileEntityComposite;if(tile!=null)tile.OnBlockAdded(pair.Key,b,pd.PrimaryId);}
   pp.PlaceLandProtectionBlock(claim,pd.PrimaryId);p.Teleport(ledger.ToVector3()+new Vector3(0,1,1),0);p.SetPosition(ledger.ToVector3(),false);
   Recruitment.Handle(p,"view","","",ledger,-1,Guid.NewGuid().ToString("N"));Check(Core.Progress.Roster.Settlements.Count==1,"connected owner registers settlement");
   var r=Core.Progress.Roster.Hire(Core.Progress.Roster.Settlements[0].Id,"Smith",Guid.NewGuid().ToString("N"));id=r.Id;r.Name="Tamsin Reed";r.Tier=3;Core.Progress.Roster.MarkFallen(r);
   var guard=Core.Progress.Roster.Hire(r.SettlementId,"Defender",Guid.NewGuid().ToString("N"));guard.Name="Bram Vale";guard.Tier=5;Core.Progress.Roster.MarkFallen(guard);Core.Save();p.Teleport(shrine.ToVector3()+new Vector3(0,0,2),180);
   SdtdConsole.Instance.Output("SHRINE "+shrine+" FORGE "+forge+" ID "+id);return;
  }
  if(id==null){var saved=Core.Progress.Roster.Recruits.Find(r=>r.Name=="Tamsin Reed");if(saved!=null){id=saved.Id;var home=Core.Progress.Roster.Settlements.Find(s=>s.Id==saved.SettlementId);claim=new Vector3i(home.X,home.Y,home.Z);shrine=claim+new Vector3i(4,0,3);forge=claim+new Vector3i(4,0,0);}}
  var rec=Core.Progress.Roster.Recruits.Find(r=>r.Id==id);if(rec==null)throw new Exception("Run setup first");
  if(args[0]=="party"){PartyChecks(w,rec);return;}
  if(args[0]=="inspect"){foreach(var r in Core.Progress.Roster.Recruits)SdtdConsole.Instance.Output("RECRUIT "+r.Id+" "+r.Name+" Tier="+r.Tier+" "+r.Status+" deaths="+r.Deaths+" ready="+r.RecoveryReadyAt);SdtdConsole.Instance.Output("LIVING="+w.EntityAlives.Count(e=>e is EntityDelveRecruit&&!e.IsDead())+" receipts="+Core.Progress.Roster.Receipts.Count);return;}
  if(args[0]=="complete"){Check(rec.Status=="Recovering","remote request started recovery");w.worldTime=rec.RecoveryReadyAt;Recruitment.Tick();Check(rec.Status=="Reserve"&&rec.Id==id&&rec.Name=="Tamsin Reed"&&rec.Tier==3&&rec.Role=="Smith"&&rec.Health==120,"remote recovery preserves full identity and tier");Core.Save();return;}
  if(args[0]=="redeploy"){Check(rec.Status=="Assigned","client assigned recovered recruit");Recruitment.Tick();Check(w.EntityAlives.Count(e=>e is EntityDelveRecruit&&!e.IsDead())==1,"exactly one living recovered body on server");return;}
  if(args[0]=="kill"){var body=w.EntityAlives.First(e=>e is EntityDelveRecruit&&!e.IsDead());body.SetDead();Recruitment.Tick();Check(rec.Status=="Fallen"&&rec.Deaths==2,"second native death retains record and increments generation");return;}
  if(args[0]=="assertfallen"){Check(rec.Status=="Fallen"&&rec.Id==id&&rec.Tier==3&&Core.Progress.Roster.Recruits.Count==2,"stale or forged network order leaves fallen record unchanged");return;}
  throw new Exception("Unknown command");
 }catch(Exception ex){SdtdConsole.Instance.Output("[ShrineAcceptance] FAIL "+ex);}}
 static void PartyChecks(World w,RecruitRecord r){
  var pp=GameManager.Instance.persistentPlayers;var s=Core.Progress.Roster.Settlements.Find(x=>x.Id==r.SettlementId);var ownerData=pp.Players.Values.First(x=>x.PrimaryId.CombinedString==s.Owner);var owner=w.GetEntity(ownerData.EntityId) as EntityPlayer;
  if(owner==null||r.Status!="Fallen")throw new Exception("Requires connected owner and fallen recruit");
  var uid=PlatformUserIdentifierAbs.FromPlatformAndId("Steam","76561198000000992",false);if(pp.GetPlayerData(uid)!=null)throw new Exception("Synthetic identity already exists");
  EntityPlayer ally=null;var saved=r.Copy();var receipts=Core.Progress.Roster.Receipts.ToList();var oldParty=owner.Party;
  try{
   ally=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),shrine.ToVector3()) as EntityPlayer;ally.world=w;w.Entities.Add(ally.entityId,ally);w.Players.Add(ally.entityId,ally);
   var data=pp.CreatePlayerData(uid,uid,"ShrineAllyFixture",(Platform.EPlayGroup)0);data.EntityId=ally.entityId;pp.MapPlayer(data);
   Action<EntityPlayer,string> order=(p,token)=>{((Dictionary<int,float>)typeof(Recruitment).GetField("requests",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic).GetValue(null)).Clear();Recruitment.Handle(p,"resurrect",s.Id,r.Id,shrine,-1,token,r.Deaths);};
   order(ally,Guid.NewGuid().ToString("N"));Check(r.Status=="Fallen","registered outsider cannot recover owner's recruit");
   pp.Allies.SetStatus(ownerData.PrimaryId,uid,AllyStore.AllyStatus.Allies);pp.Allies.SetStatus(uid,ownerData.PrimaryId,AllyStore.AllyStatus.Allies);
   order(ally,Guid.NewGuid().ToString("N"));Check(r.Status=="Fallen","ally outside current party cannot recover recruit");
   var party=new Party();party.AddPlayer(owner);party.AddPlayer(ally);
   order(ally,Guid.NewGuid().ToString("N"));Check(r.Status=="Recovering","allied current party member can begin recovery");ulong deadline=r.RecoveryReadyAt;int count=Core.Progress.Roster.Receipts.Count;
   order(owner,Guid.NewGuid().ToString("N"));order(ally,Guid.NewGuid().ToString("N"));Check(r.RecoveryReadyAt==deadline&&Core.Progress.Roster.Receipts.Count==count&&Core.Progress.Roster.Recruits.Count==2,"competing owner and ally orders commit exactly one ritual");
   Core.Progress.Roster.InterruptRecovery(r);ally.Party=null;
   order(ally,Guid.NewGuid().ToString("N"));Check(r.Status=="Fallen","leaving party revokes recovery permission immediately");
   ally.Party=party;pp.Allies.ClearStatus(ownerData.PrimaryId,uid);pp.Allies.ClearStatus(uid,ownerData.PrimaryId);
   order(ally,Guid.NewGuid().ToString("N"));Check(r.Status=="Fallen","revoked alliance rejects stale party member orders");
  }finally{
   owner.Party=oldParty;pp.Allies.ClearStatus(ownerData.PrimaryId,uid);pp.Allies.ClearStatus(uid,ownerData.PrimaryId);pp.UnmapPlayer(uid);pp.Players.Remove(uid);
   if(ally!=null){w.Entities.Remove(ally.entityId);w.Players.Remove(ally.entityId);UnityEngine.Object.Destroy(ally.gameObject);}
   Core.Progress.Roster.Recruits[Core.Progress.Roster.Recruits.FindIndex(x=>x.Id==r.Id)]=saved;Core.Progress.Roster.Receipts=receipts;Core.Save();
  }
 }
}
