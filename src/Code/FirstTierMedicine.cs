using System;
using HarmonyLib;
namespace Delve
{
    [HarmonyPatch(typeof(MinEventActionModifyStats),"execute")]
    public static class FirstTierInstantTreatment
    {
        static void Prefix(MinEventParams __0,string ___statName,MinEventActionModifyStats.OperationTypes ___operation,bool ___cvarRef,ref float ___value,out float __state)
        {
            __state=___value;
            if(__0==null || (___statName!="health" && ___statName!="stamina") || ___operation!=MinEventActionModifyStats.OperationTypes.add || ___cvarRef || ___value<=0)return;
            bool instantBuff=__0.Buff!=null && __0.Buff.BuffName=="buffDrugPainkillers";
            bool medicalItem=__0.Buff==null && __0.ItemValue!=null && __0.ItemValue.ItemClass!=null && __0.ItemValue.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse("medical,medicalSkill"));
            bool potion=__0.ItemValue!=null&&Rank20Crafting.Marked(__0.ItemValue,Rank20Crafting.Brews);if(!instantBuff && !medicalItem && !potion)return;
            var healer=instantBuff?__0.Self.world.GetEntity(__0.Buff.InstigatorId) as EntityAlive:__0.Self;
            float bonus=___statName=="health" && CharacterProgression.IsLocal(healer) && ProgressionRuntime.Has(healer,"Alchemy","MeasuredTreatment")?.1f:0;
            if(potion || (___statName=="health"&&Rank20Crafting.Marked(__0.ItemValue,Rank20Crafting.Dressings)))bonus+=.15f;___value*=1+bonus;
        }
        static Exception Finalizer(Exception __exception,ref float ___value,float __state){___value=__state;return __exception;}
    }
}

