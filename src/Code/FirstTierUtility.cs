using System;
using HarmonyLib;
using UnityEngine;
namespace Delve
{
    [HarmonyPatch(typeof(EffectManager),"GetValue")]
    public static class FirstTierWeaponCosts
    {
        static void Postfix(PassiveEffects __0,ItemValue __1,EntityAlive __3,ref float __result)
        {
            if(__0!=PassiveEffects.StaminaLoss || !CharacterProgression.IsLocal(__3) || __1==null || __1.ItemClass==null)return;
            string skill=ProficiencyRules.Identify(__1.ItemClass.GetItemName());
            string perk=skill=="Blades"?"BladeFamiliarity":skill=="Blunt"?"HeavyGrip":skill=="Polearms"?"PolearmFamiliarity":skill=="Unarmed"?"ConditionedHands":null;
            if(perk!=null && ProgressionRuntime.Has(__3,skill,perk))__result*=.9f;
        }
    }
    [HarmonyPatch(typeof(ItemValue),"ModifyValue")]
    public static class FittedArmor
    {
        public struct Before {public float Base,Percent;}
        static void Prefix(float __3,float __4,out Before __state){__state=new Before{Base=__3,Percent=__4};}
        static void Postfix(ItemValue __instance,EntityAlive __0,PassiveEffects __2,ref float __3,ref float __4,Before __state)
        {
            if(!CharacterProgression.IsLocal(__0) || __instance.ItemClass==null)return;
            string skill=null,perk=null;
            if(__instance.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse("heavyArmor"))){skill="HeavyArmor";perk="FittedPlate";}
            else if(__instance.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse("mediumArmor"))){skill="MediumArmor";perk="SuppleFit";}
            else if(__instance.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse("lightArmor"))){skill="LightArmor";perk="UnburdenedFit";}
            if(skill==null)return;
            if((__2==PassiveEffects.Mobility || __2==PassiveEffects.StaminaChangeOT) && (ProgressionRuntime.Has(__0,skill,perk)||(skill=="HeavyArmor"&&Rank20.Has(__0,skill,"MarchofIron"))))
            {__3=FirstTierRules.Relieve(__state.Base,__3,(ProgressionRuntime.Has(__0,skill,perk)?.1f:0)+(skill=="HeavyArmor"&&Rank20.Armor(__0,"heavyArmor")&&Rank20.Has(__0,skill,"MarchofIron")?.2f:0),true);__4=FirstTierRules.Relieve(__state.Percent,__4,(ProgressionRuntime.Has(__0,skill,perk)?.1f:0)+(skill=="HeavyArmor"&&Rank20.Armor(__0,"heavyArmor")&&Rank20.Has(__0,skill,"MarchofIron")?.2f:0),true);}
            if(__2==PassiveEffects.NoiseMultiplier && skill=="LightArmor" && ProgressionRuntime.Has(__0,skill,"QuietWeave"))
            {__3=FirstTierRules.Relieve(__state.Base,__3,.2f,false);__4=FirstTierRules.Relieve(__state.Percent,__4,.2f,false);}
        }
    }
    [HarmonyPatch(typeof(AIDirector),"NotifyNoise")]
    public static class SoftStepsEffect
    {
        static void Prefix(Entity __0,string __2,ref float __3)
        {
            var player=__0 as EntityPlayer;
            if(player!=null && player.Progression!=null && __2!=null && (__2.StartsWith("step",StringComparison.Ordinal) || __2=="player_swim" || __2.StartsWith("playerland",StringComparison.Ordinal)) && ProgressionRuntime.Has(player,"Stealth","SoftSteps"))__3*=.9f;
        }
    }
    public static class FirstTierHarvest
    {
        public static bool Deposit(BlockValue block)
        {
            if(block.isair)return false;string n=block.Block.GetBlockName();
            return block.isTerrain && (n=="terrStone" || n.StartsWith("terrOre",StringComparison.Ordinal) || n=="terrDirt" || n=="terrForestGround" || n=="terrBurntForestGround" || n=="terrDesertGround");
        }
        public static bool Plant(BlockValue block){return !block.isair && (block.Block is BlockPlant || block.Block.GetBlockName().StartsWith("planted",StringComparison.Ordinal));}
        public static bool Tree(BlockValue block){return !block.isair && block.Block is BlockModelTree;}
        public static bool Raw(string name)
        {
            if(name.IndexOf("seed",StringComparison.OrdinalIgnoreCase)>=0)return false;
            return name=="foodRawMeat" || name=="resourceLeather" || name=="resourceAnimalFat" || name=="resourceBone" || name=="resourceFeather" || name=="foodEgg" || name=="resourceCloth" || name=="resourceYuccaFibers" || name.StartsWith("foodCrop",StringComparison.Ordinal) || name.StartsWith("resourceCrop",StringComparison.Ordinal) || name=="foodDelveBrambleberries" || name=="resourceDelveYarrow" || name=="resourceDelveThyme" || name=="resourceDelveMooncap";
        }
    }
    [HarmonyPatch(typeof(ItemActionAttack),"GetDamageBlock")]
    public static class SoundTechnique
    {
        static void Postfix(ItemValue __0,BlockValue __1,EntityAlive __2,ref float __result)
        {
            if(!CharacterProgression.IsLocal(__2) || !FirstTierHarvest.Deposit(__1) || !__0.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse("miningTool")))return;
            float bonus=ProgressionRuntime.Has(__2,"Mining","SoundTechnique")?.1f:0;if(Rank20.Has(__2,"Mining","Stonebreaker"))bonus+=.2f;__result*=1+bonus;
            if(FirstTierCombat.Current!=null)FirstTierCombat.Current.Mining=true;
        }
    }
    [HarmonyPatch(typeof(ItemActionMelee),"ExecuteAction")]
    public static class WorkingHands
    {
        // Resolve the actual target before asking the native action to choose its
        // animation/cooldown. The shared ItemAction object is restored immediately.
        [ThreadStatic]public static EntityAlive Harvester;
        public struct State {public float Delay;public EntityAlive Previous;}
        static void Prefix(ItemActionMelee __instance,ItemActionData __0,bool __1,out State __state)
        {
            __state=new State{Delay=__instance.Delay,Previous=Harvester};
            var p=__0.invData.holdingEntity;if(__1 || !CharacterProgression.IsLocal(p) || !ProgressionRuntime.Has(p,"Farming","WorkingHands"))return;
            WorldRayHitInfo hit=__instance.GetExecuteActionTarget(__0);if(hit==null || !hit.bHitValid)return;
            var entity=ItemActionAttack.GetEntityFromHit(hit) as EntityAlive;
            bool eligible=entity!=null?entity.IsDead() && entity.HasAnyTags(FastTags<TagGroup.Global>.Parse("animal")):FirstTierHarvest.Plant(ItemActionAttack.GetBlockHit(p.world,hit));
            if(!eligible)return;
            Harvester=p;__instance.Delay/=1.1f;
        }
        static Exception Finalizer(ItemActionMelee __instance,Exception __exception,State __state){__instance.Delay=__state.Delay;Harvester=__state.Previous;return __exception;}
    }
    [HarmonyPatch(typeof(EffectManager),"GetValue")]
    public static class HarvestAnimationSpeed
    {static void Postfix(PassiveEffects __0,EntityAlive __3,ref float __result){if(__0==PassiveEffects.AttacksPerMinute && __3!=null && __3==WorkingHands.Harvester)__result*=1.1f;}}
    [HarmonyPatch(typeof(GameUtils),"HarvestOnAttack")]
    public static class HarvestContext
    {
        [ThreadStatic]public static ItemActionData Action;
        static void Prefix(ItemActionData __0,out ItemActionData __state){__state=Action;Action=__0;}
        static Exception Finalizer(Exception __exception,ItemActionData __state){Action=__state;return __exception;}
    }
    [HarmonyPatch(typeof(QuestEventManager),"HarvestedItem")]
    public static class FirstTierYield
    {
        static void Prefix(ItemStack __1,BlockValue __2)
        {
            var p=TrainingHooks.Player;if(!CharacterProgression.IsLocal(p) || __1==null || __1.count<=0 || __1.itemValue.ItemClass==null)return;
            string n=__1.itemValue.ItemClass.GetItemName();float bonus=0;string key=null;
            if(__1.itemValue.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse("quest,delveUniqueHarvest,delveRareHarvest")))return;
            var action=HarvestContext.Action;var corpse=action==null?null:action.attackDetails.entityHit as EntityAlive;
            var tool=p.inventory.holdingItemItemValue;
            if(tool!=null&&tool.ItemClass!=null&&tool.ItemClass.GetItemName()=="delveHarvestScythe"&&FirstTierHarvest.Plant(__2)&&FirstTierHarvest.Raw(n)) {bonus+=(Math.Max(1,Math.Min(6,(int)tool.Quality))-1)*.1f;key="delveHarvestCarry_"+n;}
            if(FirstTierHarvest.Raw(n) && (FirstTierHarvest.Plant(__2) || (corpse!=null && corpse.IsDead() && corpse.HasAnyTags(FastTags<TagGroup.Global>.Parse("animal")))) && ProgressionRuntime.Has(p,"Farming","CarefulHarvest")){bonus+=.1f;key="delveHarvestCarry_"+n;}
            if(n=="resourceWood" && FirstTierHarvest.Tree(__2) && ProgressionRuntime.Has(p,"Carpentry","Woodwise")){bonus=.15f;key="delveWoodCarry";}
            if(FirstTierHarvest.Plant(__2)&&__2.Block.GetBlockName().EndsWith("3HarvestPlayer",StringComparison.Ordinal)&&FirstTierHarvest.Raw(n)&&Rank20.Has(p,"Farming","GreenThumb")){bonus+=.15f;key="delveHarvestCarry_"+n;}
            if(corpse!=null&&corpse.IsDead()&&corpse.HasAnyTags(FastTags<TagGroup.Global>.Parse("animal"))&&(n=="foodRawMeat"||n=="resourceAnimalFat")&&Rank20.Has(p,"Farming","CleanButchery")){bonus+=.15f;key="delveHarvestCarry_"+n;}
            if(key==null)return;
            float carry=CharacterProgression.Get(p,key);__1.count=FirstTierRules.Yield(__1.count,ref carry,bonus);CharacterProgression.Set(p,key,carry);
        }
    }
}




