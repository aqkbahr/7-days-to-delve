using System;
using System.Collections.Generic;
using HarmonyLib;

namespace Delve
{
    public static class WayrestCampaign
    {
        public const string ReceiptPrefix = "%delveWayrestJob_";
        public static bool IsJob(string id)
        { id = (id ?? "").ToLowerInvariant(); return id == "delvewayrestfetch" || id == "delvewayrestclear" || id == "delvewayrestfetchclear"; }

        // Native player CVars persist and synchronize to the host. Receipts are
        // idempotent, so reconnect/reload/repeated completion callbacks cannot
        // count the same contract twice. Only the contract owner contributes;
        // party members still receive the normal native shared-quest rewards.
        public static void RecordCompletion(Quest q)
        {
            if (q == null || q.CurrentState != Quest.QuestState.Completed || q.SharedOwnerID != -1 || q.OwnerJournal == null) return;
            EntityPlayer p = q.OwnerJournal.OwnerPlayer;
            if (p == null || String.IsNullOrEmpty(q.QuestUniqueId)) return;
            if (IsJob(q.ID))
            {
                if (p.Buffs.GetCustomVar("delveWayrestJobs") >= 10) return;
                string key = ReceiptPrefix + q.QuestUniqueId;
                p.Buffs.SetCustomVar(key, 1, true);
            }
            else if (String.Equals(q.ID, "delveWayrestOnward", StringComparison.OrdinalIgnoreCase)) p.Buffs.SetCustomVar("%delveArborArrival", 1, true);
        }

        public static void Tick(World world)
        {
            if (!Core.IsServer || Core.Progress == null || ModManager.GetMod("DelveWayrest", true) == null) return;
            bool changed = false;
            int before = Core.Progress.WayrestReceipts.Count;
            foreach (EntityPlayer p in world.GetPlayers())
            {
                foreach (var receipt in p.Buffs.EnumerateCustomVars(ReceiptPrefix, true))
                    if (receipt.Value == 1) changed |= Core.Progress.CreditWayrest(receipt.Key, GameUtils.WorldTimeToDays(world.GetWorldTime()));
                if (Core.Progress.WayrestReceipts.Count == 10 && p.Buffs.GetCustomVar("%delveArborArrival") == 1 && !Core.Progress.ArborReached)
                { Core.Progress.ArborReached = true; changed = true; }
            }
            if (changed) Core.Save();
            TryRefurbish(world);
            foreach (EntityPlayer p in world.GetPlayers())
            {
                p.Buffs.SetCustomVar("delveWayrestJobs", Core.Progress.WayrestReceipts.Count, true);
                p.Buffs.SetCustomVar("delveWayrestReady", Core.Progress.WayrestReceipts.Count == 10 ? 1 : 0, true);
                p.Buffs.SetCustomVar("delveArborUnlocked", Core.Progress.ArborReached ? 1 : 0, true);
                if (!p.Buffs.HasBuff("delveWayrestProgress")) p.Buffs.AddBuff("delveWayrestProgress");
            }
            if (before == 0 && Core.Progress.WayrestReceipts.Count > 0)
                GameManager.Instance.ChatMessageServer(null, EChatType.Global, -1,
                    "[Wayrest Steward] Your first returned contract helps our people endure. Prepare your own refuge outside Wayrest: establish a hearth, secure food and clean water, improve equipment, and stock healing and repairs. Keep returning contracts to reclaim the frontier; champion victories advance our struggle against the Queen separately.", null,
                    EMessageSender.Server, GeneratedTextManager.BbCodeSupportMode.NotSupported);
            if (before < 10 && Core.Progress.WayrestReceipts.Count == 10)
                GameManager.Instance.ChatMessageServer(null, EChatType.Global, -1,
                    "[Delve] Wayrest: 10/10 contracts complete. Ask the Steward for the road to Arbor Camp.", null,
                    EMessageSender.Server, GeneratedTextManager.BbCodeSupportMode.NotSupported);
        }

        public static void TryRefurbish(World world)
        {
            var state = Core.Progress;
            if (state == null || state.WayrestRefurbished || state.WayrestReceipts.Count != 10 ||
                GameUtils.WorldTimeToDays(world.GetWorldTime()) <= state.WayrestCompletedDay ||
                GameUtils.WorldTimeToHours(world.GetWorldTime())*60+GameUtils.WorldTimeToMinutes(world.GetWorldTime()) < 245 ||
                GameUtils.WorldTimeToHours(world.GetWorldTime())*60+GameUtils.WorldTimeToMinutes(world.GetWorldTime()) >= 1310) return;
            // Explicit small delta on the protected authored compound, never a
            // prefab reset. Nearby claims (including offline claims) defer it.
            var players = GameManager.Instance.persistentPlayers;
            int radius = GamePrefs.GetInt(EnumGamePrefs.LandClaimSize) / 2;
            foreach (var entry in players.Players)
                foreach (var claim in entry.Value.GetLandProtectionBlocks())
                    if (claim.x + radius >= -2711 && claim.x - radius <= -2652 &&
                        claim.z + radius >= -2182 && claim.z - radius <= -2123) return;
            var changes = new List<BlockChangeInfo>();
            BlockValue oldPost = Block.GetBlockValue("woodLogPillar100", false);
            BlockValue stone = Block.GetBlockValue("cobblestoneShapes:cube", false);
            if (oldPost.isair || stone.isair) return;
            // Reinforce the two existing entrance posts; keep the gate open.
            foreach (int x in new[] { 25, 34 })
                for (int y = 2; y <= 6; y++)
                {
                    var pos = new Vector3i(-2711+x,63+y,-2182+4);
                    if (world.GetChunkSync(pos.x >> 4,pos.z >> 4) == null) return;
                    BlockValue current = world.GetBlock(pos.x,pos.y,pos.z);
                    if (current.type == stone.type) continue; // restart after a partial delta
                    if (current.type != oldPost.type) return; // preserve edited construction
                    changes.Add(new BlockChangeInfo(new BlockValueRef(pos),stone));
                }
            if (changes.Count != 0) world.SetBlocksRPC(changes);
            state.WayrestRefurbished = true;
            Core.Save();
            Log.Out("[Delve] Wayrest morning refurbishment: reinforced entrance posts; no prefab reset.");
        }
    }

    [HarmonyPatch(typeof(QuestJournal), "CompleteQuest")]
    public static class WayrestQuestCompletion
    { private static void Postfix(Quest __0) { WayrestCampaign.RecordCompletion(__0); } }

    [HarmonyPatch(typeof(EntityTrader), "PopulateActiveQuests")]
    public static class WayrestJobTier
    {
        private static void Prefix(EntityTrader __instance, ref int __1)
        {
            if (EntityClass.GetEntityClassName(__instance.entityClass) == "delveWayrestSteward") __1 = 1;
        }
    }

    [HarmonyPatch(typeof(QuestEventManager), "GetQuestList")]
    public static class WayrestBoardMilestone
    {
        private static void Postfix(World __0, int __1, int __2, ref List<Quest> __result)
        {
            // Refresh a cached pre-milestone board immediately when the shared
            // unlock arrives, rather than making a late joiner wait 24 hours.
            if (__result == null || Core.Progress == null || Core.Progress.WayrestReceipts.Count != 10) return;
            var npc = __0.GetEntity(__1);
            var player = __0.GetEntity(__2) as EntityPlayer;
            if (npc == null || player == null || EntityClass.GetEntityClassName(npc.entityClass) != "delveWayrestSteward") return;
            if (player.QuestJournal.FindCompletedQuest("delvewayrestonward", -1) || player.QuestJournal.FindActiveQuest("delvewayrestonward", -1) != null) return;
            if (!__result.Exists(q => String.Equals(q.ID,"delveWayrestOnward",StringComparison.OrdinalIgnoreCase))) __result = null;
        }
    }
}

// A normal quest-journal objective; reads the server-synchronized world tally.
public class ObjectiveDelveWayrest : BaseObjective
{
    public override bool useUpdateLoop { get { return true; } }
    public override void SetupObjective() { }
    public override void SetupDisplay() { Description = "Complete Wayrest contracts together"; StatusText = CurrentValue + "/10"; }
    public override void AddHooks() { }
    public override void RemoveHooks() { }
    public override void InternalToParametersDictionary(ref Dictionary<string, object> parameters) { }
    public override void Update(float dt) { Refresh(); }
    public override void Refresh()
    {
        if (Complete || OwnerQuest == null || OwnerQuest.OwnerJournal == null) return;
        var p = OwnerQuest.OwnerJournal.OwnerPlayer;
        if (p == null) return;
        CurrentValue = (byte)Math.Min(10, Math.Max(0, p.Buffs.GetCustomVar("delveWayrestJobs")));
        SetupDisplay();
        if (CurrentValue == 10)
        { Complete = true; OwnerQuest.RefreshQuestCompletion(QuestClass.CompletionTypes.AutoComplete, null, true, null); }
    }
    public override BaseObjective Clone() { var copy = new ObjectiveDelveWayrest(); CopyValues(copy); return copy; }
}
