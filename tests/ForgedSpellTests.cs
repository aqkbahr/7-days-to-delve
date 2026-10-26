using System;
using Delve;
class ForgedSpellTests
{
    static int checks;
    static void Check(bool value){if(!value)throw new Exception("Forged spell rule check "+checks);checks++;}
    static void Main()
    {
        Check(ForgedSpellRules.Healing(1,1,false)==25);
        Check(ForgedSpellRules.Healing(-1,-1,false)==25);
        Check(ForgedSpellRules.Healing(20,100,true)>25);
        Check(ForgedSpellRules.Healing(200,1000,true)==ForgedSpellRules.Healing(20,100,true));
        Check(ForgedSpellRules.SupportCandidate(true,true,12,.49f,true));
        Check(!ForgedSpellRules.SupportCandidate(false,true,5,0,true));
        Check(!ForgedSpellRules.SupportCandidate(true,false,5,0,true));
        Check(!ForgedSpellRules.SupportCandidate(true,true,-1,0,true));
        Check(!ForgedSpellRules.SupportCandidate(true,true,12.01f,0,true));
        Check(!ForgedSpellRules.SupportCandidate(true,true,5,.5f,true));
        Check(!ForgedSpellRules.SupportCandidate(true,true,5,0,false));
        Check(ForgedSpellRules.BurstCandidate(true,true,false,false,4,true));
        Check(!ForgedSpellRules.BurstCandidate(true,true,true,false,1,true));
        Check(!ForgedSpellRules.BurstCandidate(true,true,false,true,1,true));
        Check(!ForgedSpellRules.BurstCandidate(true,false,false,false,1,true));
        Check(!ForgedSpellRules.BurstCandidate(false,true,false,false,1,true));
        Check(!ForgedSpellRules.BurstCandidate(true,true,false,false,4.01f,true));
        Check(!ForgedSpellRules.BurstCandidate(true,true,false,false,1,false));
        Check(ProficiencyRules.Identify("delveEtchedHexRune")=="Totems");
        Check(ProficiencyRules.Identify("delveForgedCrossbow")=="Archery");
        Check(ProficiencyRules.Identify("delveForgedPickaxe")==null);
        Console.WriteLine("PASS: "+checks+" Forged targeting, healing bounds, splash exclusion and skill checks");
    }
}
