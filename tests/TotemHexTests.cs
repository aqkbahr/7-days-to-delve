using System;
using Delve;
class TotemHexTests
{
    static int checks;
    static void Check(bool value){checks++;if(!value)throw new Exception("Totem check "+checks);}
    static void Main()
    {
        Check(TotemHexRules.ImpactDamage(20)==23);
        Check(TotemHexRules.ImpactDamage(0)==0);
        Check(TotemHexRules.SplashDamage(false)==4 && TotemHexRules.SplashDamage(true)==6);
        Check(TotemHexRules.Candidate(true,true,false,false,2.25f));
        Check(!TotemHexRules.Candidate(true,true,false,false,2.251f));
        Check(!TotemHexRules.Candidate(false,true,false,false,1));
        Check(!TotemHexRules.Candidate(true,false,false,false,1));
        Check(!TotemHexRules.Candidate(true,true,true,false,1));
        Check(!TotemHexRules.Candidate(true,true,false,true,0));
        var wound=new WoundState();
        wound.Apply(0,TotemHexRules.DecayDamage,0);
        Check(wound.Tick(2.5f,5)==6);
        Check(wound.Tick(5,5)==6);
        Check(wound.Tick(6,5)==0);
        wound.Apply(7,TotemHexRules.DecayDamage,0);
        Check(wound.Tick(9.5f,5)==6);
        wound.Apply(9.5f,TotemHexRules.DecayDamage,0);
        Check(wound.Tick(9.5f,5)==0);
        Check(wound.Tick(14.5f,5)==12);
        Console.WriteLine("PASS: "+checks+" totem impact, radius, exclusions, decay and refresh checks");
    }
}
