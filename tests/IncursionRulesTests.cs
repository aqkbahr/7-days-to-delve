using System;
using Delve;
class IncursionRulesTests
{
    static int count;
    static void Check(bool value, string label) { if (!value) throw new Exception(label); count++; }
    static int Main()
    {
        Check(!IncursionRules.ArrivalWindow(true,false,1,4), "not early");
        Check(IncursionRules.ArrivalWindow(true,false,2,4), "two hours before dawn");
        Check(IncursionRules.ArrivalWindow(true,false,3,4), "retry spawn search within window");
        Check(!IncursionRules.ArrivalWindow(true,true,4,4), "never at dawn");
        Check(!IncursionRules.ArrivalWindow(false,false,2,4), "never ordinary night");
        Check(IncursionRules.ArrivalWindow(true,false,23,1), "midnight crossing with short day setting");
        Check(IncursionRules.NightId(7,23,1)==IncursionRules.NightId(8,0,1), "one attempt across midnight");
        Check(IncursionRules.NightId(8,2,4)==8, "legacy default attempt day preserved");
        Check(IncursionRules.BossHealth(1)==900 && IncursionRules.BossHealth(4)==2250, "party scaling");
        Check(IncursionRules.BossHealth(0)==900 && IncursionRules.BossHealth(30)==4050, "bounded health");
        Check(IncursionRules.Phase(0)==0 && IncursionRules.Phase(11.9f)==0, "arrival grace");
        Check(IncursionRules.Phase(12)==1 && IncursionRules.Phase(15.9f)==1, "warning");
        Check(IncursionRules.Phase(16)==2 && IncursionRules.Phase(21.9f)==2, "assault");
        Check(IncursionRules.Phase(22)==3 && IncursionRules.Phase(27.9f)==3, "recovery");
        Check(IncursionRules.Phase(28)==0 && IncursionRules.Phase(42)==1, "normal and repeat");
        Console.WriteLine("PASS: "+count+" incursion rule checks."); return 0;
    }
}
