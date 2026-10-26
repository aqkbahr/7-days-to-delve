using System;
using Delve;
class FirstTierTests
{
    static int count;
    static void Check(bool value,string name){count++;if(!value)throw new Exception(name);}
    static void Main()
    {
        var combo=new ComboState();combo.Hit(false,0);Check(combo.Count==1,"first light builds one");
        combo.Hit(false,1);Check(combo.Count==1 && combo.Expires==4,"repetition cannot refresh");
        combo.Hit(true,2);combo.Hit(false,3);Check(combo.Count==3,"alternation builds three");
        Check(!combo.Finisher(false,4) && combo.Finisher(true,4),"only heavy spends combo");
        combo.Hit(false,5);Check(combo.Expires==7,"capped repetition cannot extend combo");
        combo.Hit(true,6);Check(combo.Count==0,"finisher does not rebuild");
        combo.Hit(true,7);combo.Expire(11);Check(combo.Count==0,"exact four-second expiry");
        combo.Hit(false,12);combo.Clear();Check(!combo.Finisher(true,12) && combo.Count==0,"miss or weapon switch clears");
        var wound=new WoundState();Check(wound.Apply(0,20,2),"first wound allowed");
        Check(wound.Tick(0,6)==0,"application does not deal instant damage");
        Check(wound.Tick(1,6)==3 && wound.Tick(1,6)==0,"fractional damage paid once");
        Check(!wound.Apply(1.9f,200,2),"two-second cooldown");
        Check(wound.Apply(2,12,2),"replacement at cooldown boundary");
        Check(wound.Tick(2,6)==0,"replacement does not cash out old wound");
        Check(wound.Tick(8,6)==12 && wound.Tick(100,6)==0,"no excess damage after expiry");
        float carry=0;int yield=0;for(int i=0;i<10;i++)yield+=FirstTierRules.Yield(1,ref carry,.1f);
        Check(yield==11 && Math.Abs(carry)<.0001,"small harvests retain fractional bonus");
        carry=0;Check(FirstTierRules.Yield(20,ref carry,.15f)==23,"wood yield");
        Check(Math.Abs(FirstTierRules.Relieve(1,.8f,.1f,true)-.82f)<.0001,"reduce armor penalty only");
        Check(FirstTierRules.Relieve(1,1.2f,.1f,true)==1.2f,"never reduce positive armor bonus");
        Check(Math.Abs(FirstTierRules.Relieve(1,1.5f,.2f,false)-1.4f)<.0001,"reduce only armor noise contribution");
        int basics=0;
        foreach(string skill in ProficiencyRules.Skills)
        {
            int perSkill=0;foreach(var entry in TalentCatalog.Entries)if(entry.Value.Skill==skill && entry.Value.Rank==10)
            {
                var def=entry.Value;Check(def.Implemented,"all fundamentals implemented: "+entry.Key);
                Check(!def.CanBuy(9,false,false,k=>false),"rank nine locked");
                Check(def.CanBuy(10,false,false,k=>false),"rank ten without trials or higher prerequisites");perSkill++;basics++;
            }
            Check(perSkill==2,"starter Summoning has no talent placeholders; established skills have two fundamentals");
        }
        Check(basics==42,"forty-two fundamentals");
        Console.WriteLine("PASS: "+count+" first-tier behavior and eligibility checks.");
    }
}
