using System;
namespace DelveForest
{
    public static class ForestRules
    {
        public static bool EarlyHorde(int level,bool firstNight) { return firstNight || (level>=1 && level<=20); }
        public static string HordeGroup(string original,int level,bool firstNight)
        {
            if(!EarlyHorde(level,firstNight) || String.IsNullOrEmpty(original))return original;
            if(original.StartsWith("delveForestHorde_",StringComparison.Ordinal))return original;
            if(original.StartsWith("delveIncursion_",StringComparison.Ordinal))original=original.Substring("delveIncursion_".Length);
            return "delveForestHorde_"+original;
        }
        public static string ReplacementAtLevel(string kind,int level,int ordinal)
        {
            if(ordinal<0 || level<1)return null;
            if(kind=="imp" && level>=6 && ordinal<2)return "delveImp";
            if(ordinal!=0)return null;
            if(kind=="soldier" && level>=11)return "delvePossessedSoldier";
            if(kind=="occupation" && level>=16)return "delveDemonSpawn";
            return "delveCorruptedWalker";
        }
        public static string Replacement(string kind,int stage,int ordinal)
        {
            if(ordinal<0) return null;
            if(kind=="imp" && stage>=41 && ordinal<2) return "delveImp";
            if(ordinal!=0) return null;
            if(kind=="soldier" && stage>=41) return "delvePossessedSoldier";
            if(kind=="occupation" && stage>=81) return "delveDemonSpawn";
            return "delveCorruptedWalker";
        }
        public static string[] Encounter(string kind)
        {
            switch(kind) {
                case "corrupted": return new[]{"zombieBoe","zombieJoe","zombieNurse","delveCorruptedWalker"};
                case "room": return new[]{"zombieBoe","zombieJoe","delveCorruptedWalker"};
                case "imp": return new[]{"zombieBoe","zombieJoe","delveImp","delveImp"};
                case "soldier": return new[]{"zombieBoe","zombieJoe","delvePossessedSoldier"};
                default: return null;
            }
        }
    }
}
