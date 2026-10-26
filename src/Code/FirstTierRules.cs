using System;
namespace Delve
{
    public sealed class ComboState
    {
        public int Count; public bool LastHeavy; public float Expires;
        public void Clear(){Count=0;Expires=0;}
        public void Expire(float now){if(now>=Expires)Clear();}
        public bool Finisher(bool heavy,float now){Expire(now);return heavy && Count==3;}
        public void Hit(bool heavy,float now)
        {
            if(Finisher(heavy,now)){Clear();return;}
            if(Count==0 || (heavy!=LastHeavy && Count<3)){Count++;LastHeavy=heavy;Expires=now+4;}
        }
    }
    public sealed class WoundState
    {
        public float Start, NextAllowed; public double Total; public int Paid;
        public bool Apply(float now,double total,float cooldown)
        {if(now<NextAllowed)return false;Start=now;NextAllowed=now+cooldown;Total=total;Paid=0;return true;}
        public int Tick(float now,float duration)
        {int due=(int)Math.Floor(Total*Math.Max(0,Math.Min(1,(now-Start)/duration)));int amount=Math.Max(0,due-Paid);Paid+=amount;return amount;}
    }
    public static class FirstTierRules
    {
        public static float Relieve(float before,float after,float fraction,bool negative)
        {float delta=after-before;return (negative?delta<0:delta>0)?before+delta*(1-fraction):after;}
        public static int Yield(int count,ref float remainder,float bonus)
        {float total=count*bonus+remainder;int extra=(int)Math.Floor(total+0.00001f);remainder=total-extra;return count+extra;}
    }
}
