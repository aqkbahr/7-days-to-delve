using System;
using System.Collections.Generic;
public class ConsoleCmdForestBaseline : ConsoleCmdAbstract
{
    public override string[] getCommands(){return new[]{"forestbaseline"};}
    public override string getDescription(){return "Verify integrated Forest crafting ownership and deferred content.";}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        try {
            string[] items={"delveOakCudgel","delveAshSpear","delveLeatherKnuckles","resourceGlue","resourceCloth","resourceForgedIron","plantedCorn1"};
            string[] skills={"Carpentry","Carpentry","Carpentry","Alchemy","Carpentry","Smithing","Farming"};
            for(int i=0;i<items.Length;i++) {
                var recipe=CraftingManager.GetRecipe(items[i]);
                if(recipe==null || Delve.TrainingHooks.CraftedSkill(items[i],recipe.craftingArea)!=skills[i])throw new Exception("Ownership: "+items[i]);
            }
            foreach(string mineral in new[]{"resourceScrapIron","resourcePotassiumNitratePowder"})
                if(Delve.ForestRecipeOwnership.Harvest(mineral)!="Mining")throw new Exception("Harvest: "+mineral);
            if(CraftingManager.GetRecipe("delveArborProtection")==null||BuffManager.GetBuff("delveArborProtected")==null)throw new Exception("Arbor protection definitions missing");
            SdtdConsole.Instance.Output("[ForestBaseline] PASS 10 integrated ownership, mineral and deferred-content checks.");
        }catch(Exception ex){SdtdConsole.Instance.Output("[ForestBaseline] FAIL "+ex);}
    }
}
