using HarmonyLib;

namespace Delve
{
    // Use native trader closing, lock release, door handling and teleport volumes.
    // Do not toggle areas independently: native updates would reopen them.
    [HarmonyPatch(typeof(TraderInfo), "get_IsOpen")]
    public static class IncursionSettlement
    {
        private static void Postfix(ref bool __result)
        {
            if (GameManager.Instance == null || GameManager.Instance.World == null) return;
            if (SkyManager.IsBloodMoonVisible() && !GameManager.Instance.World.IsDaytime()) __result = false;
        }
    }
}
