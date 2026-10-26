using System;

namespace Delve
{
    public static class ProficiencyRules
    {
        public static readonly string[] Skills = { "Blades", "Blunt", "Polearms", "Archery", "Wands", "Staffs", "Totems", "Summoning", "Unarmed", "HeavyArmor", "MediumArmor", "LightArmor", "PackMule", "Athletics", "Stealth", "Farming", "Cooking", "Mining", "Smithing", "Carpentry", "Alchemy" };
        public static readonly int[] Bands = { 10, 20, 40, 60, 80, 100 };
        public static readonly int[] BandCosts = { 2, 3, 3, 3, 3, 1 };
        public const int MaxPractice = 23760;
        public static int NextCost(int rank) { return 40 + 4 * Math.Max(1, Math.Min(99, rank)); }
        public static int Threshold(int rank)
        {
            int n = Math.Max(1, Math.Min(100, rank)) - 1;
            return 40 * n + 2 * n * (n + 1);
        }
        public static int Rank(float practice)
        {
            int rank = 1;
            while (rank < 100 && practice >= Threshold(rank + 1)) rank++;
            return rank;
        }
        public static float Migrate(float damage)
        {
            if (float.IsNaN(damage) || float.IsInfinity(damage)) return 0;
            float old = Math.Max(0, Math.Min(20000, damage)) / 200;
            if (old < 1) return 0; // Old rank zero is replaced by the new baseline.
            int rank = Math.Max(1, (int)old);
            return rank >= 100 ? MaxPractice : Threshold(rank) + (old - (int)old) * NextCost(rank);
        }
        public static int AttributeBudget(int level, bool tutorial)
        { return Math.Max(0, Math.Min(80, level) - 1) + (tutorial ? 5 : 0); }
        public static int TalentBudget(int level) { return Math.Max(1, Math.Min(80, level)); }
        public static int AvailableTalents(int level, int spent)
        { return Math.Max(0, TalentBudget(level) - Math.Max(0, spent)); }
        // A merge preserves the stronger practiced discipline without adding ranks.
        public static float MergePractice(float current, float legacy)
        { return Math.Max(Credit(current,0), Credit(legacy,0)); }
        public static int TalentCapacity(int proficiency, bool masteryTrial)
        {
            int capacity=0;
            for (int i=0;i<Bands.Length;i++)
                if (proficiency>=Bands[i] && (i<5 || masteryTrial)) capacity+=BandCosts[i];
            return capacity;
        }
        public static string MilestoneKey(string category, int slot)
        {
            if (slot<1 || slot>10 || (category!="boss" && category!="reclamation" && category!="challenge")) return null;
            return "delveReward_"+category+"_"+slot;
        }
        public static string Identify(string itemName)
        {
            string name=(itemName ?? "").ToLowerInvariant();
            if(name=="delvesummoningrod" || name=="delveforgedsummoningrod" || name=="delvesummoningrune")return "Summoning";
            if (name.Contains("pickaxe")) return null;
            if(name=="delveetchedhexrune" || name=="delveetchedhealingrune" || name=="delveetchedwardrune")return "Totems";
            if (name.Contains("knuckle") || name.Contains("handplayer") || name.Contains("fist")) return "Unarmed";
            if (name.StartsWith("delve") && (name.Contains("wand") || name.Contains("staff") || name.Contains("spell"))) return name.Contains("staff") ? "Staffs" : "Wands";
            if (name.StartsWith("delve") && (name.Contains("totem") || name.Contains("ritualseal"))) return "Totems";
            if (name.StartsWith("delve") && name.Contains("chargedcore")) return "Staffs";
            if (name.StartsWith("delve") && name.Contains("arcaneshard")) return "Wands";
            if (name.Contains("spear")) return "Polearms";
            // Projectile damage can carry an ammunition ItemValue rather than
            // the launcher. Recognize arrows/bolts without consulting held gear.
            if (name.Contains("bow") || name.Contains("arrow") || name.Contains("crossbowbolt")) return "Archery";
            if (name.Contains("blade") || name.Contains("knife") || name.Contains("dagger") || name.Contains("sword")) return "Blades";
            if (name.Contains("club") || name.Contains("sledge") || name.Contains("axe") || name.Contains("mace") || name.Contains("cudgel")) return "Blunt";
            return null;
        }

        public static float Credit(float current,int damage)
        {
            if (float.IsNaN(current) || float.IsInfinity(current)) current=0;
            return Math.Min(MaxPractice,Math.Max(0,current)+Math.Max(0,damage));
        }
    }
}
