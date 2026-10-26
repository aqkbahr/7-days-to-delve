using System.Reflection;
using HarmonyLib;
using Delve;
namespace DelveStations {
 public class ModApi:IModApi {
  public void InitMod(Mod mod){new Harmony("delve.station.upgrades").PatchAll(Assembly.GetExecutingAssembly());Log.Out("[DelveStations] Native tool-slot station progression enabled.");}
 }
 [HarmonyPatch(typeof(RecipeProgression),"Allowed")]
 public static class StationRecipeGate {
  static bool Prefix(Recipe recipe,EntityAlive player,ref bool __result){
   if(recipe==null||recipe.IsScrap)return true;
   var row=Catalog.Find(ForestSliceCatalog.Key(recipe));if(row==null)return true;
   __result=player!=null&&ProficiencyRules.Rank(CharacterProgression.Get(player,"delvePractice"+row.Skill))>=row.Rank;return false;
  }
 }
 [HarmonyPatch(typeof(ForestSliceCatalog),"Rank")]
 public static class StationRanks {static void Postfix(Recipe r,ref int __result){var row=Catalog.Find(ForestSliceCatalog.Key(r));if(row!=null)__result=row.Rank;}}
 [HarmonyPatch(typeof(ForestSliceCatalog),"Minimum")]
 public static class StationMinimum {static void Postfix(string n,ref int __result){var row=Catalog.ByName(n);if(row!=null)__result=row.Rank;}}
 [HarmonyPatch(typeof(ForestSliceCatalog),"Skill")]
 public static class StationSkills {static void Postfix(string n,ref string __result){var row=Catalog.ByName(n);if(row!=null)__result=row.Skill;}}
 [HarmonyPatch(typeof(TrainingHooks),"CraftedSkill")]
 public static class StationPractice {static void Postfix(string name,string station,ref string __result){var row=Catalog.ByName(name);if(row!=null)__result=row.Skill;else if(string.IsNullOrEmpty(station)&&(string.Equals(name,"toolCookingPot",System.StringComparison.OrdinalIgnoreCase)||string.Equals(name,"toolCookingGrill",System.StringComparison.OrdinalIgnoreCase)))__result="Cooking";}}
}
