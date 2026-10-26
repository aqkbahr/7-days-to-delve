using HarmonyLib;
namespace Delve
{
    public static class RecipeProgression
    {
        public static int Minimum(string name) { return ForestSliceCatalog.Minimum(name); }
        public static bool Allowed(Recipe recipe,EntityAlive player)
        {
            if(recipe==null || player==null || recipe.IsScrap)return true;
            string recruitKey=ForestSliceCatalog.Key(recipe);
            if(recruitKey=="delverecruitledger||1|resourcewood=20" || recruitKey=="delverallyflag||1|resourcecloth=5,resourcewood=15" || recruitKey=="delverecoveryshrine||1|resourcecloth=5,resourcerocksmall=30,resourcewood=10")return true;
            if(recipe.GetName()=="delveSummoningRod" || recipe.GetName()=="delveSummoningRune")return recipe.craftingArea=="delveFieldCraftingMat" || recipe.GetName()=="delveSummoningRune" && recipe.craftingArea=="delveInscriptionKit";
            if(recipe.GetName()=="delveForgedSummoningRod")return recipe.craftingArea=="delveSawKitTier3" && ProficiencyRules.Rank(CharacterProgression.Get(player,"delvePracticeCarpentry"))>=20;
            int rank=ForestSliceCatalog.Rank(recipe);
            // This release advertises only audited Forest variants. Later native
            // facilities/recipes remain outside the first-playtest crafting menu.
            if(rank>20)return false;
            string skill=ForestSliceCatalog.Skill(recipe.GetName());
            if(skill==null)return true;
            return ProficiencyRules.Rank(CharacterProgression.Get(player,"delvePractice"+skill))>=rank;
        }

    }
    [HarmonyPatch(typeof(Recipe),"IsUnlocked")]
    public static class RecipeKnowledgeGate
    { private static void Postfix(Recipe __instance,EntityPlayer __0,ref bool __result) { __result=__result && RecipeProgression.Allowed(__instance,__0); } }
    [HarmonyPatch(typeof(Recipe),"CanCraft")]
    public static class RecipeCraftGate
    { private static void Postfix(Recipe __instance,EntityAlive __1,ref bool __result) { __result=__result && RecipeProgression.Allowed(__instance,__1); } }
    [HarmonyPatch(typeof(Recipe),"CanCraftAny")]
    public static class RecipeAnyGate
    { private static void Postfix(Recipe __instance,EntityAlive __1,ref bool __result) { __result=__result && RecipeProgression.Allowed(__instance,__1); } }
}
