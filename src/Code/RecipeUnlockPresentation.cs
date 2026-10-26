using System;
using HarmonyLib;
namespace Delve {
    // Native UnlockedBy splits an empty string into one unresolved entry.
    // The crafting UI then dereferences its null perk every refresh.
    public static class RecipeUnlockPresentation {
        public static bool Primitive(string name) {
            return name=="armorPrimitiveHelmet" || name=="armorPrimitiveOutfit" ||
                name=="armorPrimitiveGloves" || name=="armorPrimitiveBoots" ||
                name=="meleeWpnClubT0WoodenClub" || name=="gunBowT0PrimitiveBow" ||
                name=="meleeWpnBladeT0BoneKnife";
        }
        public static bool Blank(DynamicProperties properties) {
            string text;
            return properties!=null && properties.Values.TryGetValue("UnlockedBy",out text)
                && String.IsNullOrWhiteSpace(text);
        }
    }
    [HarmonyPatch(typeof(ItemClass),"get_UnlockedBy")]
    public static class ItemUnlockPresentation {
        static bool Prefix(ItemClass __instance,ref RecipeUnlockData[] __result) {
            if(!RecipeUnlockPresentation.Primitive(__instance.GetItemName()) && !RecipeUnlockPresentation.Blank(__instance.Properties))return true;
            __result=new RecipeUnlockData[0];return false;
        }
    }
    [HarmonyPatch(typeof(Block),"get_UnlockedBy")]
    public static class BlockUnlockPresentation {
        static bool Prefix(Block __instance,ref RecipeUnlockData[] __result) {
            if(!RecipeUnlockPresentation.Blank(__instance.Properties))return true;
            __result=new RecipeUnlockData[0];return false;
        }
    }
}
