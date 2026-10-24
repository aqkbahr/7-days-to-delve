using System;
using System.Collections.Generic;
namespace Delve
{
    public sealed class TalentDefinition
    {
        public readonly string Skill;
        public readonly int Rank;
        public readonly bool Implemented;
        public readonly string[] Prerequisites;
        public TalentDefinition(string skill,int rank,bool implemented,string[] prerequisites)
        { Skill=skill;Rank=rank;Implemented=implemented;Prerequisites=prerequisites; }
        public bool CanBuy(int proficiency,bool trial,bool otherMastery,Func<string,bool> owns)
        {
            if(!Implemented || proficiency<Rank || (Rank==100 && (!trial || otherMastery))) return false;
            foreach(string key in Prerequisites) if(!owns(key)) return false;
            return true;
        }
    }
    public static class ProgressionMath
    {
        public static float PackedLoad(int[] counts,int[] limits,int slots)
        {
            if(slots<=0 || counts==null || limits==null || counts.Length!=limits.Length) return 0;
            double sum=0;
            for(int i=0;i<counts.Length;i++) if(limits[i]>0) sum+=(double)Math.Max(0,counts[i])/limits[i];
            return (float)Math.Min(1,sum/slots);
        }
        public static float RecipeDuration(float baseSeconds,float intelligenceSpeed,float perkSpeed)
        { return Math.Max(0,baseSeconds)/(1+Math.Max(0,intelligenceSpeed)+Math.Max(0,perkSpeed)); }
    }
}
