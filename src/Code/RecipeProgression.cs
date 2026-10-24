using HarmonyLib;
namespace Delve
{
    public static class RecipeProgression
    {
        public static int Minimum(string name)
        {
            // Explicit authored prototype recipes. Unknown recipes retain native
            // knowledge checks until their itemization rows have been reviewed.
            switch(name)
            {
                case "delveIronDagger":case "delveIronMace":case "delveIronSpear":return 20;
                case "delveHuntingBow":return 20;
                default:return 1;
            }
        }
        public static bool Allowed(Recipe recipe,EntityAlive player)
        {
            if(recipe==null || player==null || recipe.IsScrap) return true;
            string skill=TrainingHooks.CraftedSkill(recipe.GetName(),recipe.craftingArea);
            if(skill==null) return true;
            return ProficiencyRules.Rank(CharacterProgression.Get(player,"delvePractice"+skill))>=Minimum(recipe.GetName());
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
