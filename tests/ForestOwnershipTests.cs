using System;
using Delve;
class ForestOwnershipTests
{
    static void Check(string got,string expected){if(got!=expected)throw new Exception("Expected "+expected+" got "+got);}
    static void Main()
    {
        Check(ForestRecipeOwnership.Harvest("resourceScrapIron"),"Mining");
        Check(ForestRecipeOwnership.Harvest("resourcePotassiumNitratePowder"),"Mining");
        Check(ForestRecipeOwnership.Harvest("resourceFeather"),"Farming");
        Check(ForestRecipeOwnership.Skill("delveOakCudgel"),"Carpentry");
        Check(ForestRecipeOwnership.Skill("delveAshSpear"),"Carpentry");
        Check(ForestRecipeOwnership.Skill("delveLeatherKnuckles"),"Carpentry");
        Check(ForestRecipeOwnership.Skill("resourceGlue"),"Alchemy");
        Check(ForestRecipeOwnership.Skill("resourceCloth"),"Carpentry");
        Check(ForestRecipeOwnership.Skill("resourceForgedIron"),"Smithing");
        Check(ForestRecipeOwnership.Skill("plantedCorn1"),"Farming");
        Check(ForestRecipeOwnership.Skill("delveArborProtection"),"Alchemy");
        Check(ForestRecipeOwnership.Skill(null),null);
        Console.WriteLine("PASS: 12 Forest ownership and planned-content exclusion checks");
    }
}
