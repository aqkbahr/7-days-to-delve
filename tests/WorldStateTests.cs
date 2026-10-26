using System;
using System.IO;
using Delve;

public class WorldStateTests
{
    static int checks;
    static void Check(bool ok,string description)
    { if (!ok) throw new Exception(description); checks++; Console.WriteLine("PASS " + description); }
    public static int Main(string[] args)
    {
        string dir=Path.Combine(Path.GetFullPath(args[0]),Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(dir);
        string path=Path.Combine(dir,"world.xml");
        var store=new WorldStateStore(path);
        var state=store.Load();
        Check(!state.WardenDefeated && state.CorruptedKills==0,"fresh world defaults");
        state.CorruptedKills=12; store.Save(state);
        state.CorruptedKills=13; state.WardenDefeated=true; state.LastAttemptDay=8; store.Save(state);
        var loaded=new WorldStateStore(path).Load();
        Check(loaded.CorruptedKills==13 && loaded.WardenDefeated && loaded.LastAttemptDay==8,"victory and counter survive reload");
        Check(File.Exists(path+".bak") && !File.Exists(path+".tmp"),"atomic rotation retains backup and consumes temp");
        File.WriteAllText(path,"broken xml");
        store=new WorldStateStore(path); loaded=store.Load();
        Check(store.RecoveredBackup && loaded.CorruptedKills==12,"corruption recovers previous valid snapshot");
        store.Save(loaded);
        Check(Directory.GetFiles(dir,"*.corrupt-*").Length==1,"corrupt original retained for diagnosis");
        Check(new WorldStateStore(path+".bak").Load().CorruptedKills==12,"recovery does not replace good backup with corrupt content");
        File.WriteAllText(path,"<WorldProgress><Schema>2</Schema></WorldProgress>");
        bool rejected=false;
        try { new WorldStateStore(path).Load(); } catch(UnsupportedStateVersionException) { rejected=true; }
        Check(rejected,"newer schema rejected even when older backup exists");
        string lone=Path.Combine(dir,"lone.xml"); File.WriteAllText(lone,"broken");
        rejected=false; try { new WorldStateStore(lone).Load(); } catch { rejected=true; }
        Check(rejected,"unrecoverable existing save never silently resets");
        string missing=Path.Combine(dir,"missing.xml"); File.Copy(path+".bak",missing+".bak");
        Check(new WorldStateStore(missing).Load().CorruptedKills==12,"missing primary recovers backup");
        rejected=false; loaded.CorruptedKills=-1;
        try { store.Save(loaded); } catch(InvalidDataException) { rejected=true; }
        Check(rejected,"invalid counters rejected before writing");
        Check(ProficiencyRules.Identify("meleeToolAxeT1IronFireaxe")=="Blunt","axes train Blunt");
        Check(ProficiencyRules.Identify("meleeToolPickT1IronPickaxe")==null,"mining picks do not train weapon proficiency");
        Check(ProficiencyRules.Identify("ammoArrowStone")=="Archery","arrow damage identifies Archery without held weapon");
        Check(ProficiencyRules.Identify("delveIronDagger")=="Blades","Delve dagger identifies Blades");
        foreach(string tool in new[]{"Wand","Staff","Totem"})
        {
            string skill=tool=="Staff" ? "Staffs" : tool+"s";
            Check(ProficiencyRules.Identify("delveStarter"+tool)==skill,"starter tool trains "+skill);
            Check(ProficiencyRules.Identify("delve"+tool+"Rune")==skill,"rune hit trains "+skill);
        }
        Check(ProficiencyRules.Identify("delveLeatherKnuckles")=="Unarmed","starter handwraps train Unarmed");
        Check(ProficiencyRules.Identify("delveAshSpear")=="Polearms","Delve spear identifies Polearms");
        Check(ProficiencyRules.Credit(23750,100)==23760,"proficiency caps at level 100");
        Check(ProficiencyRules.Credit(200,-5)==200,"negative damage cannot reduce or increase proficiency");
        Check(ProficiencyRules.Skills.Length==21,"all twenty-one proficiencies registered");
        Check(ProficiencyRules.Rank(0)==1,"new proficiency is usable at rank one");
        Check(ProficiencyRules.Rank(43)==1 && ProficiencyRules.Rank(44)==2,"first advancement requires 44 practice");
        Check(ProficiencyRules.NextCost(50)==240 && ProficiencyRules.NextCost(99)==436,"linear RPG curve, not exponential grind");
        for(int rank=2;rank<=100;rank++)
        {
            if(ProficiencyRules.Rank(ProficiencyRules.Threshold(rank))!=rank ||
               ProficiencyRules.Rank(ProficiencyRules.Threshold(rank)-1)!=rank-1)
                throw new Exception("Broken rank boundary "+rank);
        }
        Check(ProficiencyRules.Rank(999999)==100,"all 99 advancement boundaries and final cap");
        Check(ProficiencyRules.Credit(float.NaN,44)==44 && ProficiencyRules.Credit(float.PositiveInfinity,0)==0,"invalid persisted practice sanitized");
        Check(ProficiencyRules.Rank(ProficiencyRules.Migrate(10000))==50,"old rank fifty preserved on migration");
        Check(ProficiencyRules.Migrate(20000)==23760 && ProficiencyRules.Migrate(0)==0,"old mastery and fresh data migrate correctly");
        Check(ProficiencyRules.Migrate(10100)==ProficiencyRules.Threshold(50)+120,"partial old rank progress preserved");
        Check(ProficiencyRules.Migrate(199)==0 && ProficiencyRules.Migrate(200)==0,"old rank-zero progress maps consistently to the new usable baseline");
        Check(ProficiencyRules.AttributeBudget(1,false)==0 && ProficiencyRules.AttributeBudget(1,true)==5,"tutorial adds exactly five attribute points");
        Check(ProficiencyRules.AttributeBudget(60,true)==64 && ProficiencyRules.AttributeBudget(80,true)==84 && ProficiencyRules.AttributeBudget(99,true)==84,"attribute budget caps at eighty-four");
        Check(ProficiencyRules.AttributeBudget(30,true)==34,"level skips/reloads derive the same attribute entitlement");
        Check(ProficiencyRules.TalentCapacity(9,false)==0 && ProficiencyRules.TalentCapacity(10,false)==2,"fundamentals unlock at ten");
        Check(ProficiencyRules.TalentCapacity(20,false)==5 && ProficiencyRules.TalentCapacity(40,false)==8 && ProficiencyRules.TalentCapacity(60,false)==11 && ProficiencyRules.TalentCapacity(80,false)==14,"parallel tree budget milestones");
        Check(ProficiencyRules.TalentCapacity(100,false)==14 && ProficiencyRules.TalentCapacity(100,true)==15,"last tree point requires mastery trial");
        Check(ProficiencyRules.Identify("meleeHandPlayer")=="Unarmed" && ProficiencyRules.Identify("delveFireWand")=="Wands","new combat training classifications");
        Check(ProficiencyRules.TalentBudget(1)==1 && ProficiencyRules.TalentBudget(80)==80 && ProficiencyRules.TalentBudget(100)==80,"level-only talent entitlement");
        Check(ProficiencyRules.AvailableTalents(20,25)==0 && ProficiencyRules.AvailableTalents(30,25)==5,"legacy overspend preserved without new points");
        Check(ProficiencyRules.MergePractice(500,700)==700 && ProficiencyRules.MergePractice(700,500)==700,"merges preserve strongest practice without duplication");
        Check(ProficiencyRules.Identify("delveOakTotem")=="Totems" && ProficiencyRules.Identify("delveChargedCore")=="Staffs","independent magic families");
        var rewards=new System.Collections.Generic.HashSet<string>();
        foreach(string category in new[]{"boss","reclamation","challenge"})
            for(int slot=1;slot<=10;slot++) rewards.Add(ProficiencyRules.MilestoneKey(category,slot));
        Check(rewards.Count==30,"thirty legacy receipt keys retained for save compatibility");
        Check(!rewards.Add(ProficiencyRules.MilestoneKey("boss",1)),"repeat victory resolves to the same saved reward marker");
        Check(ProficiencyRules.MilestoneKey("boss",0)==null && ProficiencyRules.MilestoneKey("boss",11)==null && ProficiencyRules.MilestoneKey("repeatable",1)==null,"invalid or unbounded reward sources rejected");
        var campaign=new WorldProgress();
        Check(campaign.CreditWayrest("contract-a",3),"first Wayrest contract counts");
        Check(!campaign.CreditWayrest("contract-a",4),"shared duplicate and replay do not count");
        Check(!campaign.CreditWayrest(null,4),"empty receipt rejected");
        for(int i=1;i<10;i++) campaign.CreditWayrest("contract-"+i,4);
        Check(campaign.WayrestReceipts.Count==10 && campaign.WayrestCompletedDay==4,"ten jobs finish on correct day");
        Check(!campaign.CreditWayrest("contract-eleven",5),"repeatable work cannot overrun campaign");
        campaign.ArborReached=true;campaign.WayrestRefurbished=true;
        var campaignStore=new WorldStateStore(Path.Combine(dir,"wayrest.xml"));campaignStore.Save(campaign);
        campaign=campaignStore.Load();
        Check(campaign.WayrestReceipts.Count==10 && campaign.ArborReached && campaign.WayrestRefurbished,"campaign flags and receipts survive reload");
        Check(!campaign.CreditWayrest("contract-a",9),"receipt remains idempotent after restart");
        Console.WriteLine(checks+" persistence/proficiency checks passed. Evidence: "+dir);
        return 0;
    }
}

