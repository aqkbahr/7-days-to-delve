namespace Delve
{
    public static class TotemHexRules
    {
        public const float DecayDamage=12;
        public static int ImpactDamage(int damage){return (int)System.Math.Round(damage*1.15f);}
        public static int SplashDamage(bool forged){return forged?6:4;}
        public static bool Candidate(bool alive,bool enemy,bool player,bool primary,float distanceSquared)
        {return alive && enemy && !player && !primary && distanceSquared<=2.25f;}
    }
}
