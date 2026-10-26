using System;
namespace Delve
{
    public static class ForgedSpellRules
    {
        public static bool SupportCandidate(bool cooperative,bool alive,float forward,float perpendicularSquared,bool visible)
        {return cooperative && alive && forward>0 && forward<=12 && perpendicularSquared<=.49f && visible;}
        public static bool BurstCandidate(bool alive,bool enemy,bool player,bool primary,float distanceSquared,bool visible)
        {return alive && enemy && !player && !primary && distanceSquared<=4 && visible;}
        public static int Healing(int wisdom,int rank,bool attuned)
        {return Math.Min(60,(int)Math.Floor(25f*(1+.02f*(Math.Max(1,Math.Min(20,wisdom))-1))*(1+.002f*(Math.Max(1,Math.Min(100,rank))-1))*(attuned?1.1f:1)));}
    }
}
