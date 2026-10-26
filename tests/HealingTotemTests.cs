using System;
using Delve;
class HealingTotemTests
{
    static int checks;
    static void Check(bool ok,string reason){if(!ok)throw new Exception(reason);checks++;}
    static void Main()
    {
        Check(HealingTotemRules.Amount(1,1)==20,"base heal");
        Check(HealingTotemRules.Amount(20,100)>20,"advancement increases healing");
        Check(HealingTotemRules.Amount(99,999)==HealingTotemRules.Amount(20,100),"caps respected");
        Check(HealingTotemRules.Restore(95,100,20)==5,"overheal clipped");
        Check(HealingTotemRules.Restore(100,100,20)==0,"full health");
        Check(HealingTotemRules.Restore(50,100,20)==20,"wounded heal");
        Check(HealingTotemRules.Restore(0,100,20)==0,"no resurrection");
        Check(HealingTotemRules.Restore(-10,100,20)==0,"negative health");
        Check(HealingTotemRules.Restore(50,100,-20)==0,"no negative healing");
        Check(HealingTotemRules.Practice(0)==0,"no overheal practice");
        Check(HealingTotemRules.Practice(5)<HealingTotemRules.Practice(20),"credit actual restoration");
        Check(HealingTotemRules.Practice(1000)==30,"practice ceiling");
        Console.WriteLine("PASS: "+checks+" healing boundary checks");
    }
}
