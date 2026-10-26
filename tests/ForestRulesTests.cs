using System;
using DelveForest;
class ForestRulesTests
{
    static int checks;
    static void Check(bool condition,string name){if(!condition)throw new Exception(name);checks++;}
    static int Main(){
        for(int level=1;level<=20;level++) {
            Check(ForestRules.EarlyHorde(level,false),"level coverage "+level);
            Check(ForestRules.HordeGroup("feralHordeStageGS100",level,false)=="delveForestHorde_feralHordeStageGS100","high stage coverage "+level);
            Check(ForestRules.HordeGroup("delveIncursion_feralHordeStageGS1",level,false)=="delveForestHorde_feralHordeStageGS1","no double mixture "+level);
        }
        Check(!ForestRules.EarlyHorde(21,false) && ForestRules.EarlyHorde(80,true),"first night and later boundary");
        Check(ForestRules.HordeGroup("native",21,false)=="native","later horde unchanged");
        Check(ForestRules.ReplacementAtLevel("imp",5,0)=="delveCorruptedWalker" && ForestRules.ReplacementAtLevel("imp",6,1)=="delveImp","level six imp");
        Check(ForestRules.ReplacementAtLevel("soldier",10,0)=="delveCorruptedWalker" && ForestRules.ReplacementAtLevel("soldier",11,0)=="delvePossessedSoldier","level eleven soldier");
        Check(ForestRules.ReplacementAtLevel("occupation",15,0)=="delveCorruptedWalker" && ForestRules.ReplacementAtLevel("occupation",16,0)=="delveDemonSpawn","level sixteen demon");
        Check(ForestRules.ReplacementAtLevel("imp",20,2)==null && ForestRules.ReplacementAtLevel("soldier",20,1)==null,"level density invariant");
        foreach(string kind in new[]{"corrupted","imp","soldier","occupation"}){
            Check(ForestRules.Replacement(kind,1,0)=="delveCorruptedWalker","starter safety "+kind);
            Check(ForestRules.Replacement(kind,1,1)==null,"starter density "+kind);
            Check(ForestRules.Replacement(kind,500,2)==null,"maximum two replacements "+kind);
            Check(ForestRules.Replacement(kind,500,-1)==null,"invalid ordinal "+kind);
        }
        Check(ForestRules.Replacement("imp",40,1)==null,"imp threshold below");
        Check(ForestRules.Replacement("imp",41,0)=="delveImp" && ForestRules.Replacement("imp",41,1)=="delveImp","imp pair unlocked");
        Check(ForestRules.Replacement("soldier",41,0)=="delvePossessedSoldier","soldier unlock");
        Check(ForestRules.Replacement("occupation",80,0)=="delveCorruptedWalker","occupation threshold below");
        Check(ForestRules.Replacement("occupation",81,0)=="delveDemonSpawn","occupation unlock");
        Check(ForestRules.Encounter("corrupted").Length==4 && ForestRules.Encounter("room").Length==3,"corruption templates");
        Check(ForestRules.Encounter("imp").Length==4 && ForestRules.Encounter("soldier").Length==3,"special templates");
        Check(ForestRules.Encounter("missing")==null,"unknown template rejected");
        Console.WriteLine("PASS: "+checks+" Forest progression and composition checks.");return 0;
    }
}
