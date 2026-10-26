using HarmonyLib;
using UnityEngine;
namespace Delve {
 [HarmonyPatch(typeof(EntityAlive),"OnAddedToWorld")]
 public static class StewardFacing {
  static void Postfix(EntityAlive __instance){
   if(__instance.world==null||__instance.world.IsRemote()||EntityClass.GetEntityClassName(__instance.entityClass)!="delveWayrestSteward")return;
   // Allium's existing Wayrest hall has its entrance south of the service desk.
   // Apply on load too, so an already-saved NPC is repaired without respawning it.
   var p=__instance.position;if(p.x < -2711 || p.x > -2651 || p.z < -2182 || p.z > -2122)return;
   __instance.SetRotationAndStopTurning(new Vector3(0,180,0));
  }
 }
}
