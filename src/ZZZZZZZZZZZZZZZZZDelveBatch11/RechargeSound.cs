using System;using System.Collections.Generic;using HarmonyLib;using UnityEngine;
namespace DelveBatchEleven {
 [HarmonyPatch(typeof(Entity),"PlayOneShot")] public static class RechargeSound {
  static readonly Dictionary<int,float> last=new Dictionary<int,float>();
  public static bool Magic(ItemValue v){if(v==null||v.ItemClass==null)return false;var n=v.ItemClass.GetItemName();return n.StartsWith("delve")&&(n.Contains("Wand")||n.Contains("Staff")||n.Contains("Totem")||n=="delveSummoningRod");}
  static bool Prefix(Entity __instance,ref string __0){var p=__instance as EntityAlive;if(p==null||p.inventory==null||!Magic(p.inventory.holdingItemItemValue)||String.IsNullOrEmpty(__0))return true;if(__0.IndexOf("reload",StringComparison.OrdinalIgnoreCase)<0&&__0!="delveMagicRechargeWhoosh")return true;float t;last.TryGetValue(p.entityId,out t);if(Time.time-t<1.3f)return false;last[p.entityId]=Time.time;__0="delveMagicRechargeWhoosh";return true;}
 }
}
