using System;
namespace Delve {
 public static class Rank20Rules {
  public static bool LongRange(float distance,float reach){return reach>0 && distance>=reach*.7f && distance<=reach+.05f;}
  public static float CappedMovement(float slowed,float normal,float bonus){return Math.Min(normal,slowed*(1+bonus));}
  public static bool WardReady(bool threeLight,bool alive,float now,float lastHostile){return threeLight&&alive&&now-lastHostile>=8;}
  public static int BonusOutput(int count,float bonus,ref float carry){if(count<=0)return count;double sum=count*bonus+Math.Max(0,carry);int extra=(int)Math.Floor(sum+0.00001);carry=(float)(sum-extra);return count+extra;}
  public static int WoodCost(int original){return Math.Max(1,(int)Math.Ceiling(original*.9));}
 }
}
