using System.Reflection;
using HarmonyLib;

namespace DelveStationProgression {
 // Preserve the accepted skill-coverage module's gates (including its explicit
 // Alchemy-40 exception) after moving its four exact variants to tiered stations.
 [HarmonyPatch]
 public static class CoverageCompatibility {
  static bool Prepare(){return AccessTools.TypeByName("DelveCoverage.CoverageCatalog")!=null;}
  static MethodBase TargetMethod(){return AccessTools.Method(AccessTools.TypeByName("DelveCoverage.CoverageCatalog"),"Find");}
  static void Prefix(ref string __0){string original;if(__0!=null && Catalog.CoverageAliases.TryGetValue(__0,out original))__0=original;}
 }
 public class ModApi:IModApi {
  public void InitMod(Mod mod) {
   new Harmony("delve.crafting.stations").PatchAll(Assembly.GetExecutingAssembly());
   Log.Out("[CraftingStations] Frozen recipe split and proficiency 1/10/20 station progression active.");
  }
 }
 // Exact variant keys include station and ingredient quantities. Never unlock
 // another native recipe merely because its output shares an allowed name.
 [HarmonyPatch(typeof(Delve.ForestSliceCatalog),"Rank")]
 public static class RankGate {
  static bool Prefix(Recipe __0,ref int __result) {
   int rank;__result=Catalog.Ranks.TryGetValue(Delve.ForestSliceCatalog.Key(__0),out rank)?rank:21;return false;
  }
 }
 [HarmonyPatch(typeof(Delve.ForestSliceCatalog),"Minimum")]
 public static class MinimumGate {
  static bool Prefix(string __0,ref int __result) {
   int rank;if(__0!=null && Catalog.Minimum.TryGetValue(__0,out rank)){__result=rank;return false;}return true;
  }
 }
 [HarmonyPatch(typeof(Delve.ForestSliceCatalog),"Skill")]
 public static class SkillGate {
  static bool Prefix(string __0,ref string __result) {
   string skill;if(__0!=null && Catalog.Skills.TryGetValue(__0,out skill)){__result=skill;return false;}return true;
  }
 }
 [HarmonyPatch(typeof(Delve.ForestRecipeOwnership),"Skill")]
 public static class PracticeOwner {
  static bool Prefix(string __0,ref string __result) {
   string skill;if(__0!=null && Catalog.Skills.TryGetValue(__0,out skill)){__result=skill;return false;}return true;
  }
 }
 [HarmonyPatch(typeof(Delve.TrainingHooks),"CraftedSkill")]
 public static class CraftedPracticeOwner {
  static bool Prefix(string __0,ref string __result) {
   string skill;if(__0!=null && Catalog.Skills.TryGetValue(__0,out skill)){__result=skill;return false;}return true;
  }
 }
}
