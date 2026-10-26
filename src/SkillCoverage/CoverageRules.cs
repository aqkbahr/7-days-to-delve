using System;
using System.Collections.Generic;
namespace DelveCoverage {
 public static class Rules {
  public static bool Explosive(string n){return n=="thrownAmmoPipeBomb"||n=="thrownDynamite";}
  public static string MaterialSkill(string material){string n=(material??"").ToLowerInvariant();return n.Contains("metal")||n.Contains("iron")||n.Contains("steel")?"Smithing":n.Contains("stone")||n.Contains("concrete")||n.Contains("cobble")||n.Contains("brick")?"Mining":"Carpentry";}
  public static float ExplosiveMultiplier(int rank){return 1+.005f*(Math.Max(1,Math.Min(100,rank))-1);}
  public static int RepairCredit(int before,int after){return after>=0&&before>after?Math.Min(20,Math.Max(1,(before-after)/10)):0;}
  public sealed class Cooldowns {
   readonly Dictionary<string,float> next=new Dictionary<string,float>();
   public bool Take(string key,float now,float delay){float value;if(next.TryGetValue(key,out value)&&now<value)return false;if(next.Count>4096){var expired=new List<string>();foreach(var p in next)if(p.Value<=now)expired.Add(p.Key);foreach(var k in expired)next.Remove(k);if(next.Count>4096)return false;}next[key]=now+delay;return true;}
  }
 }
}
