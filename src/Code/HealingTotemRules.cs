using System;
namespace Delve
{
    public static class HealingTotemRules
    {
        public static int Amount(int wisdom,int proficiency)
        {
            return (int)Math.Floor(20f*(1+.02f*(Math.Max(1,Math.Min(20,wisdom))-1))
                *(1+.002f*(Math.Max(1,Math.Min(100,proficiency))-1)));
        }
        public static int Restore(int health,int maximum,int amount)
        { return health<=0 ? 0 : Math.Max(0,Math.Min(Math.Max(0,amount),maximum-health)); }
        public static int Practice(int restored)
        { return restored<=0 ? 0 : Math.Min(30,Math.Max(1,restored/5)); }
    }
}
