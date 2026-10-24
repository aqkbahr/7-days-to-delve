using System;
using HarmonyLib;
using UnityEngine;
namespace Delve
{
    public static class ProgressionRuntime
    {
        public static bool Owns(EntityAlive p,string key)
        {
            ProgressionValue v=p.Progression.GetProgressionValue(key);
            return v!=null && v.Level>0;
        }
        public static bool Has(EntityAlive p,string skill,string name)
        { return Owns(p,"delvePerk"+skill+name); }
        public static bool Eligible(EntityPlayerLocal p,string key)
        {
            TalentDefinition def;
            if(!TalentCatalog.Entries.TryGetValue(key,out def)) return false;
            bool other=false;
            if(def.Rank==100)
                foreach(var pair in TalentCatalog.Entries)
                    if(pair.Value.Skill==def.Skill && pair.Value.Rank==100 && pair.Key!=key && Owns(p,pair.Key)) {other=true;break;}
            if(key=="delvePerkBladesSpellblade" && CharacterProgression.Get(p,"delveLevelWands")<40 && CharacterProgression.Get(p,"delveLevelStaffs")<40) return false;
            if(key=="delvePerkBluntBattleSmith" && CharacterProgression.Get(p,"delveLevelSmithing")<40) return false;
            return def.CanBuy(ProficiencyRules.Rank(CharacterProgression.Get(p,"delvePractice"+def.Skill)),
                CharacterProgression.Get(p,"delveTrial"+def.Skill)>0,other,k=>Owns(p,k));
        }
        public static float Load(EntityPlayerLocal p)
        {
            if(p.bag==null || p.bag.SlotCount==0) return 0;
            float sum=0;
            for(int i=0;i<p.bag.SlotCount;i++)
            {
                ItemStack item=p.bag.ItemGrid.GetItem(i);
                if(item==null || item.IsEmpty() || item.itemValue.ItemClass==null) continue;
                ItemClass c=item.itemValue.ItemClass;
                if(c.HasAnyTags(FastTags<TagGroup.Global>.Parse("quest,delveZeroBurden"))) continue;
                sum+=(float)item.count/Math.Max(1,c.Stacknumber.Value);
            }
            return Math.Min(1,sum/p.bag.SlotCount);
        }
        public static void UpdateLoad(EntityPlayerLocal p)
        {
            if(!CharacterProgression.IsLocal(p) || p.Progression==null || p.Buffs==null) return;
            float load=p.IsDead()?0:Load(p);
            CharacterProgression.Set(p,"delvePackedLoad",load);
            CharacterProgression.Set(p,"delvePackedPercent",(float)Math.Floor(load*100));
            float relief=Has(p,"PackMule","BalancedLoad")?.1f:0;
            if(Has(p,"PackMule","WeightDistribution"))relief+=.15f;
            if(Has(p,"PackMule","MasterPacking"))relief+=.15f;
            // The installed native inventory penalty is 0.011 mobility per slot.
            CharacterProgression.Set(p,"delveEncumbranceRelief",Math.Max(0,CharacterProgression.Get(p,"_encumberedslots"))*.011f*Math.Min(.75f,relief));
            CharacterProgression.Set(p,"delveLoadArmor",load>=.25f && Has(p,"PackMule","SettledWeight")?5:0);
            CharacterProgression.Set(p,"delveLoadHealing",load>=.5f && Has(p,"PackMule","WellStocked")?.15f:0);
            CharacterProgression.Set(p,"delveLoadReload",load>=.5f && Has(p,"PackMule","ReadyReserves")?.15f:0);
            bool packed=load>=.75f && Has(p,"PackMule","DeepStores");
            CharacterProgression.Set(p,"delveLoadSpeed",packed?.1f:0);
            CharacterProgression.Set(p,"delveLoadNeeds",packed?-.15f:0);
            if(!p.Buffs.HasBuff("delveLoadEffects"))p.Buffs.AddBuff("delveLoadEffects");
        }
        public static float CraftSpeed(EntityPlayerLocal p,string skill)
        {
            string name=skill=="Cooking"?"KitchenPractice":skill=="Smithing"?"ForgePractice":skill=="Carpentry"?"WorkshopPractice":skill=="Alchemy"?"LaboratoryPractice":null;
            return name!=null && Has(p,skill,name)?.15f:0;
        }
    }
    [HarmonyPatch(typeof(ProgressionValue),"CanPurchase")]
    public static class TalentPurchaseGate
    {
        private static void Prefix(EntityAlive __0)
        {
            EntityPlayerLocal p=__0 as EntityPlayerLocal;
            if(CharacterProgression.IsLocal(p)) CharacterProgression.ReconcileTalents(p);
        }
        private static void Postfix(ProgressionValue __instance,EntityAlive __0,int __1,ref bool __result)
        {
            EntityPlayerLocal p=__0 as EntityPlayerLocal;
            if(!CharacterProgression.IsLocal(p) || CharacterProgression.IsAttribute(__instance.Name)) return;
            // Legacy perks/attributes remain readable for migration, not new buys.
            ProgressionClass c=__instance.ProgressionClass;
            if(c!=null && (c.IsPerk || c.IsAttribute))
                __result=__result && __1==1 && __instance.Level==0 &&
                    p.Progression.SkillPoints>=1 && ProgressionRuntime.Eligible(p,__instance.Name);
        }
    }
    [HarmonyPatch(typeof(RewardSkillPoints),"GiveReward")]
    public static class NoQuestTalentRewards
    { private static bool Prefix() { return false; } }
    [HarmonyPatch(typeof(EntityPlayerLocal),"OnUpdateLive")]
    public static class LoadTick
    { private static void Postfix(EntityPlayerLocal __instance) { ProgressionRuntime.UpdateLoad(__instance); } }
    [HarmonyPatch(typeof(XUiM_Recipes),"GetRecipeCraftTime")]
    public static class ProductionSpeed
    {
        private static void Postfix(XUi __0,Recipe __1,ref float __result)
        {
            EntityPlayerLocal p=__0.playerUI.entityPlayer;
            if(!CharacterProgression.IsLocal(p) || __1==null) return;
            string skill=TrainingHooks.CraftedSkill(__1.GetName(),__1.craftingArea);
            float extra=ProgressionRuntime.CraftSpeed(p,skill);
            if(extra<=0) return;
            ProgressionValue v=p.Progression.GetProgressionValue("delveAttIntelligence");
            float intel=v==null?0:.02f*Math.Max(0,v.CalculatedLevel(p)-1);
            // Replace only our existing Intelligence factor, retaining native modifiers.
            __result*= (1+intel)/(1+intel+extra);
        }
    }
    [HarmonyPatch(typeof(EffectManager),"GetValue")]
    public static class MovementStaminaEffects
    {
        private static readonly FastTags<TagGroup.Global> Run=FastTags<TagGroup.Global>.Parse("running");
        private static readonly FastTags<TagGroup.Global> Swim=FastTags<TagGroup.Global>.Parse("swimming,swimmingRun");
        private static void Postfix(PassiveEffects __0,EntityAlive __3,FastTags<TagGroup.Global> __5,ref float __result)
        {
            if(__0!=PassiveEffects.StaminaChangeOT || !CharacterProgression.IsLocal(__3)) return;
            EntityPlayerLocal p=(EntityPlayerLocal)__3;
            bool swim=__5.Test_AnySet(Swim),run=__5.Test_AnySet(Run);
            if(__result<0 && (run || swim))
            {
                float reduction=ProgressionRuntime.Has(p,"Athletics","EfficientMotion")?.10f:0;
                if(swim && ProgressionRuntime.Has(p,"Athletics","EfficientStroke")) reduction+=.20f;
                if(run && !swim)
                {
                    if(ProgressionRuntime.Has(p,"Athletics","DistanceRunner")) reduction+=.10f;
                    if(CharacterProgression.Get(p,"delvePackedLoad")>=.25f && ProgressionRuntime.Has(p,"PackMule","TrailSupplies")) reduction+=.10f;
                }
                __result*=1-Math.Min(.5f,reduction);
            }
            else if(__result>0 && !run && !swim)
            {
                float bonus=ProgressionRuntime.Has(p,"Athletics","SteadyRecovery")?.15f:0;
                if(CharacterProgression.Get(p,"delvePackedLoad")>=.5f && ProgressionRuntime.Has(p,"PackMule","MeasuredPace"))bonus+=.20f;
                __result*=1+bonus;
            }
        }
    }

}
