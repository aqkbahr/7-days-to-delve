using HarmonyLib;using System.Reflection;using Delve;
namespace DelveBatchFive {
 public class ModApi:IModApi {public void InitMod(Mod mod){new Harmony("delve.batch.five").PatchAll(Assembly.GetExecutingAssembly());Log.Out("[Batch05] Field Crafting Mat and starter balance active.");}}
 [HarmonyPatch(typeof(ForestSliceCatalog),"Rank")] public static class Rank { [HarmonyPriority(Priority.Last)] static void Postfix(Recipe r,ref int __result){var row=Catalog.Find(ForestSliceCatalog.Key(r));if(row!=null)__result=row.Rank;} }
 [HarmonyPatch(typeof(RecipeProgression),"Allowed")] public static class Gate {static bool Prefix(Recipe recipe,EntityAlive player,ref bool __result){if(recipe==null||recipe.IsScrap)return true;var row=Catalog.Find(ForestSliceCatalog.Key(recipe));if(row==null)return true;__result=player!=null && ProficiencyRules.Rank(CharacterProgression.Get(player,"delvePractice"+row.Skill))>=row.Rank;return false;}}
 [HarmonyPatch(typeof(ForestSliceCatalog),"Minimum")] public static class Minimum { [HarmonyPriority(Priority.Last)] static void Postfix(string n,ref int __result){var r=Catalog.ByName(n);if(r!=null)__result=r.Rank;} }
 [HarmonyPatch(typeof(ForestSliceCatalog),"Skill")] public static class Skill { [HarmonyPriority(Priority.Last)] static void Postfix(string n,ref string __result){var r=Catalog.ByName(n);if(r!=null)__result=r.Skill;} }
 [HarmonyPatch(typeof(TrainingHooks),"CraftedSkill")] public static class Practice { [HarmonyPriority(Priority.Last)] static void Postfix(string name,ref string __result){var r=Catalog.ByName(name);if(r!=null)__result=r.Skill;} }
 // Keep delve verify's original assertions, updated to the shipped balance.
 [HarmonyPatch(typeof(StarterEquipment),"Verify")] public static class StarterChecks {static bool Prefix(ref int __result){__result=StarterValidation.Verify();return false;}}
}
