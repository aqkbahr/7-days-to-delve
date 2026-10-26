using System;
using System.IO;
using Delve;
public class ResurrectionTests
{
    static int checks;
    static void Check(bool ok,string name){if(!ok)throw new Exception(name);checks++;Console.WriteLine("PASS "+name);}
    static bool Reject(Action run){try{run();return false;}catch{return true;}}
    public static void Main(string[] args)
    {
        var state=new WorldProgress();var roster=state.Roster;
        roster.Settlements.Add(new SettlementRecord{Id="home",Owner="owner",X=0,Y=60,Z=0});
        roster.Settlements.Add(new SettlementRecord{Id="refuge",Owner="owner",X=100,Y=60,Z=100});
        var r=roster.Hire("home","Defender","hire");r.Name="Oren Ash";r.Tier=3;
        string identity=r.Id;roster.Assign(r,"home",1,60,1,"delveRallyFlag");
        roster.MarkFallen(r);roster.MarkFallen(r);
        Check(r.Deaths==1 && r.Status=="Fallen" && r.Health==0 && r.Station==null,"death recorded once and station released");
        Check(Reject(()=>roster.BeginRecovery(r,"home",5,60,5,100,"stale",0)),"stale death-generation request rejected");
        roster.BeginRecovery(r,"refuge",105,60,105,100,"rite-one",1);
        Check(r.Status=="Recovering" && r.SettlementId=="home" && r.RecoverySettlementId=="refuge" && r.RecoveryReadyAt==1100,"ritual starts without prematurely moving ownership");
        Check(r.Id==identity && r.Name=="Oren Ash" && r.Role=="Defender" && r.Tier==3,"ritual preserves identity name role and tier");
        Check(Reject(()=>roster.Assign(r,"refuge",101,60,101,"delveRallyFlag")),"recovering recruit cannot be assigned");
        Check(Reject(()=>roster.BeginRecovery(r,"home",6,60,6,100,"second",1)),"concurrent second ritual for same recruit rejected");
        var other=roster.Hire("home","Cook","hire-other");roster.MarkFallen(other);
        Check(Reject(()=>roster.BeginRecovery(other,"refuge",105,60,105,100,"occupied",1)),"occupied shrine rejects another recruit");
        Check(!roster.CompleteRecovery(r,1099) && r.Health==0,"no early resurrection");
        var directory=Path.Combine(args[0],Guid.NewGuid().ToString("N"));Directory.CreateDirectory(directory);
        var store=new WorldStateStore(Path.Combine(directory,"world.xml"));store.Save(state);state=store.Load();roster=state.Roster;r=roster.Recruits[0];other=roster.Recruits[1];
        Check(r.Id==identity && r.Tier==3 && r.RecoveryReadyAt==1100 && r.RecoveryReceipt=="rite-one","pending ritual and higher tier survive save reload");
        Check(roster.CompleteRecovery(r,1100),"ritual completes at deadline");
        Check(r.Status=="Reserve" && r.Health==240 && r.Id==identity && r.Tier==3 && r.Name=="Oren Ash" && r.Role=="Defender" && r.SettlementId=="refuge","same person returns at full health to destination reserve");
        Check(r.Station==null && r.RecoveryReadyAt==0 && r.RecoveryReceipt==null && roster.Recruits.Count==2,"completion clears ritual without duplicating body record");
        Check(!roster.CompleteRecovery(r,2000),"completion is idempotent");
        Check(Reject(()=>roster.BeginRecovery(r,"refuge",105,60,105,2000,"living",1)),"living recruit cannot be resurrected");
        store.Save(state);state=store.Load();roster=state.Roster;r=roster.Recruits[0];other=roster.Recruits[1];
        Check(r.Id==identity && r.Tier==3 && r.Status=="Reserve" && r.Health==240,"completed resurrection survives reload");
        roster.MarkFallen(r);
        Check(Reject(()=>roster.BeginRecovery(r,"refuge",105,60,105,2000,"rite-one",2)),"old successful receipt cannot resurrect a later death");
        Check(Reject(()=>roster.BeginRecovery(r,"refuge",105,60,105,2000,"late-packet",1)),"old life request rejected after another death");
        roster.BeginRecovery(r,"refuge",105,60,105,2000,"rite-two",2);roster.InterruptRecovery(r);
        Check(r.Status=="Fallen" && r.Id==identity && r.Tier==3 && r.Deaths==2 && r.SettlementId=="refuge","interruption retains fallen identity tier and ownership");
        roster.BeginRecovery(other,"refuge",105,60,105,2100,"other-rite",1);
        Check(other.Status=="Recovering","interruption frees shrine for another recruit");
        roster.InterruptRecovery(other);roster.BeginRecovery(r,"refuge",105,60,105,2200,"rite-three",2);
        Check(roster.CompleteRecovery(r,3200) && r.Id==identity && r.Tier==3 && r.Deaths==2,"subsequent death and retry preserve original identity");
        string legacy=Path.Combine(directory,"legacy.xml");
        File.WriteAllText(legacy,"<WorldProgress><Schema>1</Schema><Roster><Settlements><SettlementRecord><Id>old</Id><Owner>owner</Owner></SettlementRecord></Settlements><Recruits><RecruitRecord><Id>legacy-person</Id><SettlementId>old</SettlementId><Name>Legacy</Name><Role>Smith</Role><Tier>1</Tier><Health>0</Health><Status>Fallen</Status></RecruitRecord></Recruits></Roster></WorldProgress>");
        var old=new WorldStateStore(legacy).Load().Roster;old.BeginRecovery(old.Recruits[0],"old",1,60,1,1,"legacy-rite",0);
        Check(old.CompleteRecovery(old.Recruits[0],1001) && old.Recruits[0].Id=="legacy-person","pre-resurrection fallen save remains recoverable");
        roster.BeginRecovery(other,"refuge",105,60,105,4000,"corrupt-check",1);other.RecoveryReceipt="missing";
        Check(Reject(()=>store.Save(state)),"malformed pending ritual rejected before saving");
        Console.WriteLine(checks+" resurrection checks passed.");
    }
}
