using System;
using HarmonyLib;
using UnityEngine;

namespace Delve
{
    // Native bandages/poultices heal through a CVar-driven buff, bypassing
    // EntityHeal. Scale the actual newly applied treatment once by its healer.
    [HarmonyPatch(typeof(EntityAlive),"FireEvent")]
    public static class MedicalWisdom
    {
        public struct Treatment { public EntityAlive Target; public float Before; public float BeforeSpeed; public bool Bleeding; }
        private static void Prefix(EntityAlive __instance, MinEventTypes __0, out Treatment __state)
        {
            __state=new Treatment();
            if (!CharacterProgression.IsLocal(__instance) || (__0!=MinEventTypes.onSelfPrimaryActionEnd && __0!=MinEventTypes.onSelfSecondaryActionEnd)) return;
            MinEventParams context=__instance.MinEventContext;
            if (context == null || context.ItemValue == null || context.ItemValue.ItemClass == null) return;
            string item=context.ItemValue.ItemClass.GetItemName();
            if (!context.ItemValue.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse("medical,medicalSkill")) && !item.StartsWith("medical",StringComparison.Ordinal) && item!="delveHealingPoultice") return;
            EntityAlive target=__0==MinEventTypes.onSelfPrimaryActionEnd ? __instance : context.Other;
            if (target==null || target.IsDead()) return;
            __state.Target=target;
            __state.Before=CharacterProgression.Get(target,"medicalRegHealthAmount");
            __state.BeforeSpeed=CharacterProgression.Get(target,"medRegHealthIncSpeed");
            __state.Bleeding=target.Buffs.HasBuff("buffInjuryBleeding");
        }
        private static void Postfix(EntityAlive __instance, Treatment __state)
        {
            if (__state.Target==null) return;
            EntityPlayerLocal healer=(EntityPlayerLocal)__instance;
            if (CharacterProgression.Get(__state.Target,"medicalRegHealthAmount")>__state.Before)
            {
                ProgressionValue wisdom=healer.Progression.GetProgressionValue("delveAttWisdom");
                float multiplier=1+.02f*Math.Max(0,wisdom.CalculatedLevel(healer)-1);
                if(ProgressionRuntime.Has(healer,"Alchemy","MeasuredTreatment")) multiplier+=.10f;
                multiplier*=1+CharacterProgression.Get(__state.Target,"delveLoadHealing");
                float after=CharacterProgression.Get(__state.Target,"medicalRegHealthAmount");
                float speed=CharacterProgression.Get(__state.Target,"medRegHealthIncSpeed");
                float blended=(__state.Before*Math.Max(0,__state.BeforeSpeed)+(after-__state.Before)*speed*multiplier)/after;
                CharacterProgression.Set(__state.Target,"medRegHealthIncSpeed",blended);
            }
            if (__state.Bleeding && !__state.Target.Buffs.HasBuff("buffInjuryBleeding"))
                CharacterProgression.Practice(healer,"Alchemy",10);
        }
    }
    [HarmonyPatch(typeof(MinEventActionModifyStats),"execute")]
    public static class MedicalPractice
    {
        private static void Prefix(MinEventParams __0, string ___refCvarName, out int __state)
        {
            __state=-1;
            if (__0!=null && CharacterProgression.IsLocal(__0.Self) && __0.Buff!=null &&
                __0.Buff.BuffName=="buffHealHealth" && ___refCvarName=="medRegHealthIncSpeed") __state=__0.Self.Health;
        }
        private static void Postfix(MinEventParams __0, int __state)
        {
            if (__state<0) return;
            // Only credit locally attributed treatment; receiving another
            // player's medicine is not practicing Medicine yourself.
            if (__0.Buff.InstigatorId!=__0.Self.entityId) return;
            int restored=__0.Self.Health-__state;
            if (restored>0) CharacterProgression.Practice((EntityPlayerLocal)__0.Self,"Alchemy",restored);
        }
    }
    public static class TrainingHooks
    {
        public static EntityPlayerLocal Player
        {
            get { return GameManager.Instance == null || GameManager.Instance.World == null ? null : GameManager.Instance.World.GetPrimaryPlayer(); }
        }
        public static string CraftedSkill(string name, string station)
        {
            name = (name ?? "").ToLowerInvariant();
            if(name=="delvesummoningrod" || name=="delveforgedsummoningrod")return "Carpentry";
            if(ForestSliceCatalog.Minimum(name)<=20)return ForestSliceCatalog.Skill(name);
            string forged=ForgedCatalog.Skill(name);if(forged!=null)return forged;
            if(ForestProcessingCatalog.Rank(name)>0)return ForestProcessingCatalog.Skill(name);
            if(FarmingCatalog.Level(name)>0)return FarmingCatalog.Skill(name);
            string authored=ForestRecipeOwnership.Skill(name);
            if(authored!=null)return authored;
            string pantry=ForestPantryCatalog.Skill(name);
            if(pantry!=null)return pantry;
            station = (station ?? "").ToLowerInvariant();
            if (name.StartsWith("delveheritage") || name == "delvefieldguide") return null;
            if (name.StartsWith("delve") && name.EndsWith("rune")) return "Alchemy";
            if(name.StartsWith("delve") && (name.Contains("arcaneshard") || name.Contains("chargedcore") || name.Contains("ritualseal"))) return "Alchemy";
            if(name.StartsWith("armor"))
            {
                ItemValue armor=ItemClass.GetItem(name,true);
                if(armor!=null && armor.ItemClass!=null && armor.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse("mediumArmor,lightArmor"))) return "Carpentry";
            }
            if (name.Contains("draught") || name.Contains("potion") || name.StartsWith("drug") || station.Contains("chem")) return "Alchemy";
            if (name.StartsWith("medical") || name.Contains("poultice")) return "Alchemy";
            if (name.Contains("seed") || name.Contains("farmplot")) return "Farming";
            if (name.StartsWith("food") || name.StartsWith("drink") || name.Contains("tea")) return "Cooking";
            if (name.StartsWith("delve") && (name.Contains("wand") || name.Contains("staff") || name.Contains("totem"))) return "Carpentry";
            if (name.Contains("bow") || name.Contains("arrow") || name.Contains("wood") || name.Contains("frame")) return "Carpentry";
            if (station.Contains("forge") || name.StartsWith("melee") || name.StartsWith("armor") || ProficiencyRules.Identify(name) != null) return "Smithing";
            return null;
        }
    }
    // These quest events fire on actual output/harvest, not on starting a queue,
    // opening a workstation, empty swings, picking up items or creative grants.
    [HarmonyPatch(typeof(QuestEventManager),"CraftedItem")]
    public static class CraftPractice
    {
        private static void Postfix(ItemStack __0)
        {
            EntityPlayerLocal p = TrainingHooks.Player;
            if (!CharacterProgression.IsLocal(p) || __0 == null || __0.count <= 0 || __0.itemValue.ItemClass == null) return;
            string name = __0.itemValue.ItemClass.GetItemName();
            Recipe recipe = CraftingManager.GetRecipe(name);
            if (recipe == null || recipe.IsScrap) return;
            string skill = TrainingHooks.CraftedSkill(name,recipe.craftingArea);
            if (skill == null) return;
            // Per-recipe output count prevents arrow stacks from counting as
            // dozens of full crafts. Complex recipes remain more rewarding.
            int practice = (int)Math.Ceiling(Math.Min(200,20 + recipe.craftingTime * 2) * __0.count / Math.Max(1,recipe.count));
            CharacterProgression.Practice(p,skill,Math.Max(1,practice));
        }
    }
    [HarmonyPatch(typeof(QuestEventManager),"HarvestedItem")]
    public static class HarvestPractice
    {
        private static void Postfix(ItemValue __0, ItemStack __1, BlockValue __2)
        {
            EntityPlayerLocal p = TrainingHooks.Player;
            if (!CharacterProgression.IsLocal(p) || __1 == null || __1.count <= 0 || __1.itemValue.ItemClass == null) return;
            string output = __1.itemValue.ItemClass.GetItemName().ToLowerInvariant();
            string skill = ForestRecipeOwnership.Harvest(output);
            if (output == "resourcewood") skill = "Carpentry";
            else if (output == "foodrawmeat" || output == "resourceleather" || output == "resourceanimalfat" || output == "resourcebone") skill = "Farming";
            else if (output == "resourcerocksmall" || output == "resourcescrapiron" || output == "resourcecoal" || output == "resourcepotassiumnitratepowder" || output == "resourcelead" || output == "resourceoilshale" || output == "resourceclaylump") skill = "Mining";
            if (skill==null && (output.StartsWith("food") || output.StartsWith("resourcedelve") || output.Contains("goldenrod") || output.Contains("chrysanthemum") || output.Contains("cotton") || output.Contains("aloe"))) skill="Farming";
            if (skill != null) CharacterProgression.Practice(p,skill,Math.Min(20,Math.Max(1,__1.count/2)));
        }
    }
    [HarmonyPatch(typeof(EntityAlive),"DamageEntity",new Type[] { typeof(DamageSource),typeof(int),typeof(bool),typeof(float) })]
    public static class ArmorPractice
    {
        private static void Prefix(EntityAlive __instance, out int __state)
        { __state = __instance.IsDead() ? 0 : __instance.Health; }
        private static void Postfix(EntityAlive __instance, DamageSource __0, int __state)
        {
            EntityPlayerLocal p = __instance as EntityPlayerLocal;
            if (!CharacterProgression.IsLocal(p) || p.IsDead() || __0 == null || __state <= p.Health) return;
            EntityAlive attacker = p.world.GetEntity(__0.getEntityId()) as EntityAlive;
            if (attacker == null || attacker is EntityPlayer || !attacker.EntityClass.bIsEnemyEntity) return;
            int heavy=0, medium=0, light=0;
            foreach (ItemValue armor in p.equipment.GetArmor())
            {
                if (armor == null || armor.ItemClass == null) continue;
                if (armor.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse("heavyArmor"))) heavy++;
                else if (armor.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse("mediumArmor"))) medium++;
                else if (armor.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse("lightArmor"))) light++;
            }
            int count=heavy+medium+light;
            if (count == 0) return;
            int amount=Math.Min(30,Math.Max(1,(__state-p.Health)/2));
            if (heavy>0) CharacterProgression.Practice(p,"HeavyArmor",Math.Max(1,amount*heavy/count));
            if (medium>0) CharacterProgression.Practice(p,"MediumArmor",Math.Max(1,amount*medium/count));
            if (light>0) CharacterProgression.Practice(p,"LightArmor",Math.Max(1,amount*light/count));
        }
    }
    [HarmonyPatch(typeof(EntityPlayerLocal),"OnUpdateLive")]
    public static class TravelPractice
    {
        private static EntityPlayerLocal lastPlayer;
        private static Vector3 lastPosition;
        private static float lastTime;
        private static void Postfix(EntityPlayerLocal __instance)
        {
            EntityPlayerLocal p=__instance;
            float now=Time.realtimeSinceStartup;
            if (lastPlayer != p) { lastPlayer=p; lastPosition=p.position; lastTime=now; return; }
            if (now-lastTime<5) return;
            float elapsed=now-lastTime;
            float distance=(p.position-lastPosition).magnitude;
            lastTime=now; lastPosition=p.position;
            // Exclude teleports, mounted travel, long load pauses and standing.
            if (p.IsDead() || p.AttachedToEntity != null || elapsed>10 || distance<3 || distance>60) return;
            CharacterProgression.Practice(p,"Athletics",Math.Min(25,(int)distance));
            if(ProgressionRuntime.Load(p)>=.25f) CharacterProgression.Practice(p,"PackMule",Math.Min(25,(int)distance));
            if (!p.IsCrouching) return;
            foreach (EntityAlive enemy in p.world.EntityAlives)
            {
                if (enemy == null || enemy.IsDead() || !enemy.EntityClass.bIsEnemyEntity || (enemy.position-p.position).sqrMagnitude>225) continue;
                if (enemy.GetAttackTarget() == p) return;
            }
            foreach (EntityAlive enemy in p.world.EntityAlives)
                if (enemy != null && !enemy.IsDead() && enemy.EntityClass.bIsEnemyEntity && (enemy.position-p.position).sqrMagnitude<=225)
                { CharacterProgression.Practice(p,"Stealth",Math.Min(8,(int)distance)); break; }
        }
    }
}
