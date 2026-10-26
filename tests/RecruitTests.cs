using System;
using System.IO;
using Delve;
public class RecruitTests
{
    static int checks;
    static void Check(bool c,string message){if(!c)throw new Exception(message);checks++;Console.WriteLine("PASS "+message);}
    static bool Reject(Action action){try{action();return false;}catch{return true;}}
    public static void Main(string[] args)
    {
        var state=new WorldProgress();var roster=state.Roster;
        roster.Settlements.Add(new SettlementRecord{Id="home",Owner="persistent-owner",X=1,Y=60,Z=2});
        roster.Settlements.Add(new SettlementRecord{Id="second",Owner="persistent-owner",X=100,Y=60,Z=100});
        var smith=roster.Hire("home","Smith","receipt-1");var smith2=roster.Hire("home","Smith","receipt-2");
        Check(smith.Id!=smith2.Id && smith.Tier==1,"repeat hires have unique permanent identities");
        Check(Reject(()=>roster.Hire("home","Smith","receipt-1")) && roster.Recruits.Count==2,"replayed hire cannot duplicate recruit");
        Check(Reject(()=>roster.Hire("unknown","Cook","receipt-3")),"unknown settlement rejected");
        Check(Reject(()=>roster.Hire("home","Queen","receipt-3")),"unknown role rejected");
        roster.Assign(smith,"home",2,60,2,"delveForgeAnvil");
        Check(Reject(()=>roster.Assign(smith2,"home",2,60,2,"delveForgeAnvil")),"one worker per station enforced");
        Check(Reject(()=>roster.Assign(smith2,"home",3,60,2,"campfire")),"incompatible station rejected");
        roster.Assign(smith,"second",101,60,100,"delveForgeAnvil");
        roster.Assign(smith2,"home",2,60,2,"delveForgeAnvil");
        Check(smith.SettlementId=="second" && smith2.Status=="Assigned","transfer frees original station");
        var defender=roster.Hire("home","Defender","receipt-3");roster.Assign(defender,"home",5,60,5,"delveRallyFlag");
        Check(Reject(()=>roster.Assign(defender,"home",6,60,5,"forge")),"defenders cannot operate crafting stations");
        defender.Status="Fallen";defender.Health=0;defender.Station=null;
        Check(Reject(()=>roster.Assign(defender,"home",5,60,5,"delveRallyFlag")),"fallen recruit cannot be silently resurrected");
        smith.Health=47;smith.Status="Displaced";smith.Station=null;
        string dir=Path.Combine(args[0],Guid.NewGuid().ToString("N"));Directory.CreateDirectory(dir);
        var store=new WorldStateStore(Path.Combine(dir,"world.xml"));store.Save(state);var loaded=store.Load();
        Check(loaded.Roster.Recruits[0].Id==smith.Id && loaded.Roster.Recruits[0].Health==47 && loaded.Roster.Recruits[0].Status=="Displaced","identity, health and displacement survive save/load");
        Check(loaded.Roster.Recruits[2].Status=="Fallen" && loaded.Roster.Receipts.Count==3,"fallen records and hire receipts survive save/load");
        string old=Path.Combine(dir,"legacy.xml");File.WriteAllText(old,"<WorldProgress><Schema>1</Schema></WorldProgress>");
        Check(new WorldStateStore(old).Load().Roster.Recruits.Count==0,"legacy worlds acquire empty roster without losing progress");
        loaded.Roster.Recruits[1].Id=smith.Id;
        Check(Reject(()=>store.Save(loaded)),"duplicate identity rejected before save");
        Console.WriteLine(checks+" recruitment checks passed.");
    }
}
