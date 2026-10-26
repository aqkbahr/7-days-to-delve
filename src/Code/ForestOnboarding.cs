using System;using HarmonyLib;
namespace Delve {
 public static class ForestOnboarding {
  public static bool Starter(string name){switch(name){case "delveBoneDagger":case "delveOakCudgel":case "delveAshSpear":case "delveLeatherKnuckles":case "delveBorderBow":case "delveStarterWand":case "delveStarterStaff":case "delveStarterTotem":case "delveMendingTotem":return true;default:return false;}}
 }
 [HarmonyPatch(typeof(ObjectiveCraft),"Current_CraftItem")]
 public static class ForestWeaponChoice {
  static void Prefix(ObjectiveCraft __instance,ref ItemStack __0){
   if(__instance.OwnerQuest==null||!String.Equals(__instance.OwnerQuest.ID,"delveArrival",StringComparison.OrdinalIgnoreCase)||!String.Equals(__instance.ID,"delveBoneDagger",StringComparison.OrdinalIgnoreCase)||__0==null||__0.itemValue.ItemClass==null||!ForestOnboarding.Starter(__0.itemValue.ItemClass.GetItemName()))return;
   // Only the event argument changes. Inventory and every other quest keep the
   // real crafted item; native phase/count/completion checks still run.
   __0=new ItemStack(ItemClass.GetItem("delveBoneDagger",false),__0.count);
  }
 }
 [HarmonyPatch(typeof(ObjectiveCraft),"SetupDisplay")]
 public static class ForestWeaponChoiceLabel {
  static void Postfix(ObjectiveCraft __instance){if(__instance.OwnerQuest!=null&&String.Equals(__instance.OwnerQuest.ID,"delveArrival",StringComparison.OrdinalIgnoreCase)&&String.Equals(__instance.ID,"delveBoneDagger",StringComparison.OrdinalIgnoreCase))__instance.Description="Craft any starter weapon (your choice)";}
 }
}
