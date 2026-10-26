using System;
using HarmonyLib;
using UnityEngine;

namespace Delve
{
    // Local-player authority matches native progression. All durable data lives in
    // the same player save as native skill points; no entity-ID keyed player file.
    public static class CharacterProgression
    {
        public static readonly string[] Attributes = { "Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma" };
        public static bool IsAttribute(string name) { return name != null && name.StartsWith("delveAtt", StringComparison.OrdinalIgnoreCase); }
        public static bool IsLocal(EntityAlive p) { return p is EntityPlayerLocal && !p.isEntityRemote; }
        public static float Get(EntityAlive p, string key) { return p.Buffs.GetCustomVar(key); }
        public static void Set(EntityAlive p, string key, float value)
        { if (p.Buffs.GetCustomVar(key)!=value) p.Buffs.SetCustomVar(key, value, true); }
        public static int UnspentAttributes(EntityPlayerLocal p)
        {
            int spent = 0;
            foreach (string name in Attributes)
            {
                ProgressionValue v = p.Progression.GetProgressionValue("delveAtt" + name);
                if (v != null) spent += Math.Max(0, v.Level - 1);
            }
            return Math.Max(0, ProficiencyRules.AttributeBudget(p.Progression.Level, Get(p,"delveTutorialAward") > 0) - spent);
        }
        public static void Initialize(EntityPlayerLocal p)
        {
            if (!IsLocal(p) || p.Progression == null || p.Buffs == null) return;
            if (Get(p,"delveProgressionVersion") < 1)
            {
                // Refund native talent currency previously spent on prototype
                // attributes, preserving the ranks. Those ranks now consume the
                // attribute budget; a migrated overspend earns no further points
                // until caught up (or can be refunded by a normal respec).
                int refund = 0;
                foreach (string name in Attributes)
                {
                    ProgressionValue v = p.Progression.GetProgressionValue("delveAtt" + name);
                    if (v == null) return; // XML not loaded yet; do not mark migrated.
                    for (int rank = 2; rank <= Math.Min(5,v.Level); rank++) refund += (int)Math.Pow(1.14,rank);
                }
                p.Progression.SkillPoints += refund + 1;
                foreach (string skill in ProficiencyRules.Skills)
                {
                    Set(p,"delvePractice" + skill, ProficiencyRules.Migrate(Get(p,"delveDamage" + skill)));
                    RefreshSkill(p,skill);
                }
                Set(p,"delveProgressionVersion",1);
            }
            if (Get(p,"delveProgressionVersion") < 2)
            {
                // Preserve source CVars for diagnosis; never multiply legacy Magic
                // across three skills. Its progress transfers to Wands only.
                string[] sources = { "Magic", "Hunting", "Medicine" };
                string[] targets = { "Wands", "Farming", "Alchemy" };
                for (int i=0;i<sources.Length;i++)
                {
                    Set(p,"delvePractice"+targets[i],ProficiencyRules.MergePractice(
                        Get(p,"delvePractice"+targets[i]),Get(p,"delvePractice"+sources[i])));
                    p.Buffs.RemoveBuff("delveSkill"+sources[i]);
                }
                // Light retains its old rank. New Medium starts at baseline.
                Set(p,"delveLegacyUnspentTalents",p.Progression.SkillPoints);
                foreach (string skill in ProficiencyRules.Skills) RefreshSkill(p,skill);
                Set(p,"delveProgressionVersion",2);
            }
            RefreshSkill(p,"Summoning");
            ReconcileTalents(p);
            if (p.QuestJournal != null && (p.QuestJournal.FindCompletedQuest("delveEmbers", -1) || p.QuestJournal.FindCompletedQuest("delveembers", -1))) Set(p,"delveTutorialAward",1);

            Set(p,"delveAttributePoints",UnspentAttributes(p));
            if (!p.Buffs.HasBuff("delveAdvancement")) p.Buffs.AddBuff("delveAdvancement");
            p.Progression.ExpDeficit = 0;
        }
        // Legacy campaign receipt API. Receipts never grant talent currency.
        public static bool AwardMilestone(EntityPlayerLocal p, string category, int slot)
        {
            string key = ProficiencyRules.MilestoneKey(category,slot);
            if (!IsLocal(p) || key == null) return false;
            if (Get(p,key) > 0) return false;
            Set(p,key,1);
            // Campaign receipts remain saved; they no longer award talent points.
            p.bPlayerStatsChanged = true;
            return true;
        }
        public static int SpentTalents(EntityPlayerLocal p)
        {
            int spent=0;
            foreach (ProgressionValue v in p.Progression.GetDict().Values)
            {
                ProgressionClass c=v.ProgressionClass;
                if (c==null || IsAttribute(v.Name) || (!c.IsPerk && !c.IsAttribute)) continue;
                for(int rank=c.IsAttribute ? 2 : 1;rank<=v.Level;rank++)
                    spent+=Math.Max(0,c.CalculatedCostForLevel(rank));
            }
            return spent;
        }
        public static void ReconcileTalents(EntityPlayerLocal p)
        {
            int spent=SpentTalents(p);
            p.Progression.SkillPoints=ProficiencyRules.AvailableTalents(p.Progression.Level,spent);
            Set(p,"delveTalentDebt",Math.Max(0,spent-ProficiencyRules.TalentBudget(p.Progression.Level)));
        }
        public static void RefreshSkill(EntityPlayerLocal p, string skill)
        {
            int rank = ProficiencyRules.Rank(Get(p,"delvePractice" + skill));
            Set(p,"delveLevel" + skill,rank);
            Set(p,"delveBonus" + skill,(rank - 1) * .002f);
            if (!p.Buffs.HasBuff("delveSkill" + skill)) p.Buffs.AddBuff("delveSkill" + skill);
        }
        public static void Practice(EntityPlayerLocal p, string skill, int amount)
        {
            if (!IsLocal(p) || p.IsDead() || amount <= 0 || Array.IndexOf(ProficiencyRules.Skills,skill) < 0) return;
            Initialize(p);
            Set(p,"delvePractice" + skill,ProficiencyRules.Credit(Get(p,"delvePractice" + skill),amount));
            RefreshSkill(p,skill);
        }
        public static bool BuyAttribute(EntityPlayerLocal p, ProgressionValue value, int requested)
        {
            Initialize(p);
            if (!IsAttribute(value.Name) || requested != value.Level + 1 || requested > 20 || UnspentAttributes(p) < 1) return false;
            value.Level = requested;
            if (!ConnectionManager.Instance.IsServer)
                ConnectionManager.Instance.SendToServer(NetPackageManager.GetPackage<NetPackageEntitySetSkillLevelServer>().Setup(p.entityId,value.Name,value.Level),false);
            Set(p,"delveAttributePoints",UnspentAttributes(p));
            p.bPlayerStatsChanged = true;
            return true;
        }
    }

    [HarmonyPatch(typeof(XUiC_SkillAttributeLevel),"btnBuy_OnPress")]
    public static class AttributePurchase
    {
        private static bool Prefix(XUiC_SkillAttributeLevel __instance)
        {
            ProgressionValue value = __instance.CurrentSkill;
            if (value == null || !CharacterProgression.IsAttribute(value.Name)) return true;
            EntityPlayerLocal p = __instance.xui.playerUI.entityPlayer;
            CharacterProgression.BuyAttribute(p,value,__instance.Level);
            __instance.WindowGroup.Controller.RefreshBindingsSelfAndChildren();
            __instance.WindowGroup.Controller.SetAllChildrenDirty();
            return false;
        }
    }
    [HarmonyPatch(typeof(XUiC_SkillAttributeLevel),"GetBindingValueInternal")]
    public static class AttributePurchaseText
    {
        private static void Postfix(XUiC_SkillAttributeLevel __instance, ref string __0, string __1, ref bool __result)
        {
            ProgressionValue value = __instance.CurrentSkill;
            if (value == null || !CharacterProgression.IsAttribute(value.Name)) return;
            EntityPlayerLocal p = __instance.xui.playerUI.entityPlayer;
            if (__1 == "buytooltip")
            {
                __0 = "Costs 1 attribute point. Available: " + CharacterProgression.UnspentAttributes(p) + ". Talent points are separate.";
                __result = true;
            }
            else if (__1 == "buyicon" && __instance.Level>value.Level)
            {
                __0=__instance.Level==value.Level+1 && CharacterProgression.UnspentAttributes(p)>0 ? "ui_game_symbol_shopping_cart" : "ui_game_symbol_lock";
                __result=true;
            }
        }
    }
    [HarmonyPatch(typeof(ProgressionValue),"CanPurchase")]
    public static class AttributeEligibility
    {
        private static void Postfix(ProgressionValue __instance, EntityAlive __0, int __1, ref bool __result)
        {
            EntityPlayerLocal local = __0 as EntityPlayerLocal;
            if (CharacterProgression.IsLocal(local))
            {
                CharacterProgression.ReconcileTalents(local);
                if (!CharacterProgression.IsAttribute(__instance.Name) &&
                    local.Progression.SkillPoints < __instance.CostForNextLevel) __result=false;
            }
            if (!CharacterProgression.IsAttribute(__instance.Name)) return;
            EntityPlayerLocal p = __0 as EntityPlayerLocal;
            __result = p != null && __1 == __instance.Level + 1 && __1 <= 20 && CharacterProgression.UnspentAttributes(p) > 0;
        }
    }
    [HarmonyPatch(typeof(QuestJournal),"CompleteQuest")]
    public static class TutorialAdvancement
    {
        private static void Postfix(QuestJournal __instance, Quest __0)
        {
            if (__0 == null || !String.Equals(__0.ID,"delveEmbers",StringComparison.OrdinalIgnoreCase) || !CharacterProgression.IsLocal(__instance.OwnerPlayer)) return;
            CharacterProgression.Set(__instance.OwnerPlayer,"delveTutorialAward",1);
            CharacterProgression.Initialize(__instance.OwnerPlayer);
        }
    }
    [HarmonyPatch(typeof(Progression),"AddXPDeficit")]
    public static class NoDeathExperienceLoss
    {
        private static bool Prefix(Progression __instance, EntityAlive ___parent)
        {
            if (!CharacterProgression.IsLocal(___parent)) return true;
            __instance.ExpDeficit = 0;
            return false;
        }
    }
    [HarmonyPatch(typeof(Progression),"ResetProgression")]
    public static class PreservePracticeOnRespec
    {
        private static void Postfix(EntityAlive ___parent)
        {
            EntityPlayerLocal p = ___parent as EntityPlayerLocal;
            if (!CharacterProgression.IsLocal(p)) return;
            // Attribute XML has zero native cost so it cannot refund talent points.
            // Its separate balance is derived from ranks and returns automatically.
            CharacterProgression.Initialize(p);
            foreach (string skill in ProficiencyRules.Skills) CharacterProgression.RefreshSkill(p,skill);
        }
    }
    [HarmonyPatch(typeof(EntityPlayerLocal),"OnUpdateLive")]
    public static class ProgressionTick
    {
        private static EntityPlayerLocal lastPlayer;
        private static float nextTick;
        private static void Postfix(EntityPlayerLocal __instance)
        {
            if (lastPlayer != __instance) { lastPlayer = __instance; nextTick = 0; }
            if (Time.realtimeSinceStartup < nextTick) return;
            nextTick = Time.realtimeSinceStartup + 2;
            CharacterProgression.Initialize(__instance);
        }
    }
}
