using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Xml.Serialization;
using HarmonyLib;
using UnityEngine;

namespace Delve
{
    // World progress is server-owned. Player proficiency CVars use the game's
    // existing player save/network system; only the attacking local client earns it.
    public class ModApi : IModApi
    {
        public void InitMod(Mod mod)
        {
            new Harmony("delve.livingborder").PatchAll(typeof(ModApi).Assembly);
            ModEvents.GameStartDone.RegisterHandler(Core.Start);
            ModEvents.GameUpdate.RegisterHandler(Core.Update);
            ModEvents.WorldShuttingDown.RegisterHandler(Core.Stop);
            ModEvents.EntityKilled.RegisterHandler(Core.Killed);
            Log.Out("[Delve] Living Border 0.3.0-dev progression foundation initialized; full perk behaviors remain in development. Use 'delve status' in a world.");
        }
    }

    public static class Core
    {
        public static WorldProgress Progress;
        private static WorldStateStore store;
        private static float nextTick;
        private static int activeBoss = -1;
        private static bool manualEncounter;
        private static float encounterStarted;
        private static int bossPhase = -1;
        private static bool ready;
        private static readonly HashSet<int> countedDeaths = new HashSet<int>();
        private static readonly HashSet<int> participants = new HashSet<int>();
        private static readonly HashSet<int> fallenParticipants = new HashSet<int>();
        public const string BossClass = "delveAshboundWarden";
        public static readonly string[] Skills = ProficiencyRules.Skills;
        private static World World { get { return GameManager.Instance == null ? null : GameManager.Instance.World; } }
        public static bool IsServer { get { return World != null && !World.IsRemote(); } }

        public static void Start(ref ModEvents.SGameStartDoneData data)
        {
            ready = false; Progress = null; activeBoss = -1; nextTick = 0; bossPhase = -1;
            countedDeaths.Clear(); participants.Clear(); fallenParticipants.Clear();
            if (!IsServer) return;
            store = new WorldStateStore(Path.Combine(GameIO.GetSaveGameDir(), "Delve", "world.xml"));
            try
            {
                Progress = store.Load();
                // Keep native replacement/deactivation behavior; only change count.
                GamePrefs.Set(EnumGamePrefs.LandClaimCount, 2);
                GameStats.Set(EnumGameStats.LandClaimCount, 2);
                ready = true;
                Save();
                Log.Out("[Delve] World state ready: " + Status());
            }
            catch (Exception ex)
            {
                // Fail closed: never replace an unreadable campaign with defaults.
                Progress = null;
                ready = false;
                Log.Error("[Delve] World progress disabled to protect existing save: " + ex.Message);
            }
        }

        public static void Save()
        {
            if (ready && Progress != null) store.Save(Progress);
        }

        public static string Status()
        {
            if (!ready || Progress == null) return "Delve world state is not ready. Check the host log.";
            return "Living Border | Corrupted defeated: " + Progress.CorruptedKills +
                " | Ashbound Warden: " + (Progress.WardenDefeated ? "DEFEATED (saved)" : activeBoss >= 0 ? "ACTIVE" : "undefeated") +
                " | Wayrest: " + Progress.WayrestReceipts.Count + "/10 | Arbor reached: " + Progress.ArborReached +
                " | Two active Settlement Stones per player.";
        }

        public static string VerifyDefinitions()
        {
            if (!ready || !IsServer) return "World must finish loading before verification.";
            int checks = 0;
            string[] crafted = { "delveBoneDagger", "delveOakCudgel", "delveAshSpear", "delveBorderBow",
                "delveIronDagger", "delveIronMace", "delveIronSpear", "delveHuntingBow", "delveHealingPoultice",
                "delveWayfarerTea", "delveWardDraught", "delveFieldGuide", "delveHeritageHuman", "delveHeritageElf",
                "delveHeritageDwarf", "delveHeritageHalfling", "delveHeritageOrc", "delveHeritageTiefling" };
            foreach (string name in crafted)
            {
                ItemValue item = ItemClass.GetItem(name, false);
                if (item == null || item.type == 0 || item.ItemClass.GetItemName() != name)
                    throw new InvalidDataException("Missing loaded item: " + name);
                checks++;
                if (CraftingManager.GetRecipe(name) == null) throw new InvalidDataException("Missing recipe: " + name);
                checks++;
                if (Localization.Get(name) == name) throw new InvalidDataException("Missing localization: " + name);
                checks++;
            }
            foreach (string name in new[] { "delveArrival", "delveHearth", "delveEmbers" })
            {
                if (QuestClass.CreateQuest(name) == null) throw new InvalidDataException("Missing quest: " + name);
                checks++;
            }
            foreach (string name in new[] { "delveCorruptedWalker", "delvePossessedSoldier", "delveImp", "delveHellhound", "delveDemonSpawn", "delveWarpedBrute", BossClass })
            {
                int id = EntityClass.FromString(name);
                if (EntityClass.GetEntityClassName(id) != name) throw new InvalidDataException("Missing entity: " + name);
                checks++;
            }
            foreach (string name in CharacterProgression.Attributes)
            {
                ProgressionClass attribute;
                if (!Progression.ProgressionClasses.TryGetValue("delveAtt"+name,out attribute) || attribute.MinLevel!=1 || attribute.MaxLevel!=20 || attribute.CalculatedCostForLevel(20)!=0)
                    throw new InvalidDataException("Attribute framework failed: " + name);
                checks++;
            }
            foreach(var pair in TalentCatalog.Entries)
            {
                ProgressionClass perk;
                if(!Progression.ProgressionClasses.TryGetValue(pair.Key,out perk) || perk.MaxLevel!=1 || perk.CalculatedCostForLevel(1)!=1)
                    throw new InvalidDataException("Missing/incorrect talent: "+pair.Key);
                checks++;
            }
            if (Progression.MaxLevel!=80 || ProficiencyRules.TalentCapacity(100,true)!=15) throw new InvalidDataException("Advancement caps failed.");
            checks++;
            return "PASS: " + checks + " loaded content and progression-framework checks. Combat/UI/multiplayer playtest still required.";
        }

        public static string SpawnPatrol(EntityPlayer player)
        {
            if (!ready || !IsServer || player == null || player.IsDead()) return "A living player is required.";
            int offset=0;
            foreach (string name in new[] { "delveCorruptedWalker", "delveDemonSpawn", "delveHellhound" })
            {
                Vector3 position=player.position + new Vector3(15+offset,0,15);
                position.y=World.GetHeightAt(position.x,position.z)+1;
                EntityAlive enemy=EntityFactory.CreateEntity(EntityClass.FromString(name),position) as EntityAlive;
                if (enemy != null) { World.SpawnEntityInWorld(enemy); enemy.SetAttackTarget(player,600); }
                offset+=3;
            }
            return "Three corrupted enemies approach. Harvest their remains for Ember Salts.";
        }

        private static void Broadcast(string text)
        {
            Log.Out("[Delve] " + text);
            GameManager.Instance.ChatMessageServer(null, EChatType.Global, -1,
                "[Delve] " + text, null, EMessageSender.Server, GeneratedTextManager.BbCodeSupportMode.NotSupported);
        }

        public static string SpawnBoss(EntityPlayer player, bool manual)
        {
            if (!ready || !IsServer) return "Run this on the host after the world has loaded.";
            if (Progress.WardenDefeated) return "The Warden is already defeated in this world. Start a fresh test world to replay its campaign.";
            if (activeBoss >= 0) return "An encounter is already active.";
            if (player == null || player.IsDead()) return "A living player must be in the world. Dedicated console: delve boss <entityId>.";
            if (World.IsWithinTraderArea(new Vector3i(player.position))) return "Leave the NPC settlement before starting an incursion encounter.";
            Vector3 position;
            if (!TrySpawnPosition(player, out position)) return "No safe loaded spawn position found. Move into open terrain and retry.";
            int classId = EntityClass.FromString(BossClass);
            if (EntityClass.GetEntityClassName(classId) != BossClass) return "Warden entity definition was not loaded; check XML errors.";
            EntityAlive boss = EntityFactory.CreateEntity(classId, position) as EntityAlive;
            if (boss == null) return "Could not create the encounter.";
            World.SpawnEntityInWorld(boss);
            activeBoss = boss.entityId; manualEncounter = manual; encounterStarted = Time.realtimeSinceStartup; bossPhase = -1;
            participants.Clear(); fallenParticipants.Clear();
            foreach (EntityPlayer p in World.GetPlayers())
                if (!p.IsDead() && !World.IsWithinTraderArea(new Vector3i(p.position)) && (p.position - player.position).sqrMagnitude <= 250 * 250) participants.Add(p.entityId);
            participants.Add(player.entityId);
            boss.Buffs.SetCustomVar("delveBossHealth", IncursionRules.BossHealth(participants.Count), true);
            boss.Buffs.AddBuff("delveWardenScaling");
            boss.Stats.Health.BaseMax = IncursionRules.BossHealth(participants.Count);
            boss.Health = boss.GetMaxHealth();
            boss.SetAttackTarget(player, 600);
            int dawn = GameUtils.CalcDuskDawnHours(GameStats.GetInt(EnumGameStats.DayLightLength)).Item2;
            Progress.LastAttemptDay = IncursionRules.NightId(GameUtils.WorldTimeToDays(World.GetWorldTime()), GameUtils.WorldTimeToHours(World.GetWorldTime()), dawn);
            Save();
            Broadcast("The Ashbound Warden has arrived near " + player.EntityName + ". Defeat it before dawn; a fallen party must try again. Prototype encounter uses a vanilla model.");
            return "Warden spawned at " + position + ". " + (manual ? "Manual test: ten-minute limit replaces the dawn timer." : "Incursion encounter active.");
        }

        private static bool TrySpawnPosition(EntityPlayer player, out Vector3 position)
        {
            position = Vector3.zero;
            for (int attempt = 0; attempt < 12; attempt++)
            {
                int x, y, z;
                if (!World.FindRandomSpawnPointNearPlayer(player, 24, out x, out y, out z, 48)) continue;
                Vector3 candidate = new Vector3(x, y, z);
                if (World.GetChunkSync(x >> 4, z >> 4) == null || World.IsWithinTraderArea(new Vector3i(candidate))) continue;
                if ((candidate - player.position).sqrMagnitude < 18 * 18) continue;
                position = candidate; return true;
            }
            return false;
        }

        private static void TickBoss(EntityAlive boss)
        {
            int phase = IncursionRules.Phase(Time.realtimeSinceStartup - encounterStarted);
            if (phase != bossPhase)
            {
                foreach (string buff in new[] { "delveWardenWindup", "delveWardenAssault", "delveWardenRecovery" }) boss.Buffs.RemoveBuff(buff);
                bossPhase = phase;
                if (phase == 1) { boss.Buffs.AddBuff("delveWardenWindup"); Broadcast("The Warden braces for an assault! Make space; counterattack after its rush."); }
                if (phase == 2) boss.Buffs.AddBuff("delveWardenAssault");
                if (phase == 3) boss.Buffs.AddBuff("delveWardenRecovery");
            }
            EntityPlayer nearest = null;
            float distance = float.MaxValue;
            foreach (int id in participants)
            {
                EntityPlayer p = World.GetEntity(id) as EntityPlayer;
                if (p == null || p.IsDead() || fallenParticipants.Contains(id)) continue;
                float d = (p.position - boss.position).sqrMagnitude;
                if (d < distance) { distance = d; nearest = p; }
            }
            if (nearest != null) boss.SetAttackTarget(nearest, 600);
        }

        private static void Withdraw(string reason)
        {
            if (activeBoss >= 0 && World.GetEntity(activeBoss) != null)
                World.RemoveEntity(activeBoss, EnumRemoveEntityReason.Despawned);
            activeBoss = -1; participants.Clear(); fallenParticipants.Clear();
            Save();
            Broadcast("The Warden withdraws: " + reason + ". It remains undefeated and can return.");
        }

        public static void Update(ref ModEvents.SGameUpdateData data)
        {
            if (!ready || !IsServer || Time.realtimeSinceStartup < nextTick) return;
            nextTick = Time.realtimeSinceStartup + 1;
            try
            {
                int day = GameUtils.WorldTimeToDays(World.GetWorldTime());
                WayrestCampaign.Tick(World);
                int hour = GameUtils.WorldTimeToHours(World.GetWorldTime());
                int dawn = GameUtils.CalcDuskDawnHours(GameStats.GetInt(EnumGameStats.DayLightLength)).Item2;
                // Recover orphaned encounter entities after a crash/restart. Do not
                // silently adopt a stale runtime ID as a different new entity.
                foreach (EntityAlive entity in new List<EntityAlive>(World.EntityAlives))
                    if (entity != null && !entity.IsDead() && entity.entityClass == EntityClass.FromString(BossClass) && entity.entityId != activeBoss)
                        World.RemoveEntity(entity.entityId, EnumRemoveEntityReason.Despawned);

                foreach (EntityPlayer p in World.GetPlayers())
                {
                    p.Buffs.SetCustomVar("delveWorldKills", Progress.CorruptedKills, true);
                    p.Buffs.SetCustomVar("delveWardenDefeated", Progress.WardenDefeated ? 1 : 0, true);
                    if (!p.Buffs.HasBuff("delveWorldJournal")) p.Buffs.AddBuff("delveWorldJournal");
                    if (Progress.WardenDefeated && !p.Buffs.HasBuff("delveWardenVictory")) p.Buffs.AddBuff("delveWardenVictory");
                }
                if (activeBoss >= 0)
                {
                    EntityAlive boss = World.GetEntity(activeBoss) as EntityAlive;
                    if (boss == null) { Withdraw("the encounter was unloaded"); return; }
                    if (boss.IsDead()) { CompleteBoss(); return; }
                    bool someoneStanding = false;
                    foreach (int id in participants)
                    {
                        EntityPlayer p = World.GetEntity(id) as EntityPlayer;
                        if (p == null || p.IsDead()) fallenParticipants.Add(id);
                        if (p != null && !p.IsDead() && !fallenParticipants.Contains(id)) someoneStanding = true;
                    }
                    if (!someoneStanding) { Withdraw("all participating adventurers fell or left"); return; }
                    if ((!manualEncounter && World.IsDaytime()) || (manualEncounter && Time.realtimeSinceStartup - encounterStarted > 600))
                    { Withdraw(manualEncounter ? "the ten-minute test window ended" : "dawn has broken"); return; }
                    TickBoss(boss);
                    return;
                }
                if (Progress.WardenDefeated) return;
                int moonDay = GameStats.GetInt(EnumGameStats.BloodMoonDay);
                if (day == moonDay && World.IsDaytime() && day != Progress.LastScoutingDay)
                {
                    Progress.LastScoutingDay = day; Save();
                    Broadcast("Scouts report corrupted infantry, skittering imps and rare hounds, soldiers and brutes. Settlements close tonight. Prepare ammunition, repairs and healing; the Warden arrives two hours before dawn.");
                }
                if (IncursionRules.ArrivalWindow(SkyManager.IsBloodMoonVisible(), World.IsDaytime(), hour, dawn) && IncursionRules.NightId(day,hour,dawn) != Progress.LastAttemptDay)
                    foreach (EntityPlayer p in World.GetPlayers())
                        if (!p.IsDead()) { SpawnBoss(p, false); if (activeBoss >= 0) break; }
            }
            catch (Exception ex) { Log.Error("[Delve] Update failed: " + ex); nextTick += 30; }
        }

        public static void Killed(ref ModEvents.SEntityKilledData data)
        {
            if (!ready || !IsServer || data.KilledEntitiy == null) return;
            Entity dead = data.KilledEntitiy;
            if (participants.Contains(dead.entityId)) fallenParticipants.Add(dead.entityId);
            if (!countedDeaths.Add(dead.entityId)) return;
            string name = EntityClass.GetEntityClassName(dead.entityClass);
            if (name != null && name.StartsWith("delve", StringComparison.Ordinal))
            {
                Progress.CorruptedKills++;
                if (dead.entityId == activeBoss && name == BossClass) CompleteBoss();
                else Save();
            }
        }

        private static void CompleteBoss()
        {
            if (Progress.WardenDefeated) return;
            Progress.WardenDefeated = true; activeBoss = -1;
            participants.Clear(); fallenParticipants.Clear(); Save();
            Broadcast("The Ashbound Warden falls! This world's first boss victory is saved. The full ten-boss campaign is still to come.");
        }

        public static void Stop(ref ModEvents.SWorldShuttingDownData data)
        {
            if (ready && IsServer)
            {
                if (activeBoss >= 0 && World.GetEntity(activeBoss) != null)
                    World.RemoveEntity(activeBoss, EnumRemoveEntityReason.Despawned);
                Save();
            }
            ready = false; activeBoss = -1;
        }
    }

    [HarmonyPatch(typeof(EntityAlive), "DamageEntity", new Type[] { typeof(DamageSource), typeof(int), typeof(bool), typeof(float) })]
    public static class ProficiencyDamage
    {
        private static void Prefix(EntityAlive __instance, out int __state)
        { __state = __instance.IsDead() ? 0 : __instance.Health; }

        private static void Postfix(EntityAlive __instance, DamageSource __0, int __state)
        {
            if (__state <= 0 || __instance is EntityPlayer || __0 == null || __instance.world == null) return;
            int dealt = Math.Min(__state, __state - Math.Max(0,__instance.Health));
            if (dealt <= 0 || !__instance.EntityClass.bIsEnemyEntity) return;
            EntityPlayer player = __instance.world.GetEntity(__0.getEntityId()) as EntityPlayer;
            // Damage may be calculated on the attacker client. Never award on both
            // client and server; the native player CVars are saved by the game.
            if (!(player is EntityPlayerLocal) || player.isEntityRemote || __0.AttackingItem == null) return;
            ItemClass item = __0.AttackingItem.ItemClass;
            if (item == null) return;
            string skill = ProficiencyRules.Identify(item.GetItemName());
            if (skill == null) return;
            // Normalize damage into practice. Credit is capped per hit so an
            // overpowered weapon does not skip the learning curve in one swing.
            CharacterProgression.Practice((EntityPlayerLocal)player,skill,Math.Min(30,Math.Max(1,dealt/5)));
        }
    }
}

// Host/admin command only; ordinary players cannot spawn bosses or alter saves.
public class ConsoleCmdDelve : ConsoleCmdAbstract
{
    public override string[] getCommands() { return new[] { "delve" }; }
    public override string getDescription() { return "Delve playtest: status | verify | boss [playerEntityId] | patrol [playerEntityId] | save"; }
    public override void Execute(List<string> args, CommandSenderInfo senderInfo)
    {
        try
        {
            string action = args.Count == 0 ? "status" : args[0].ToLowerInvariant();
            if (action == "status") { SdtdConsole.Instance.Output(Delve.Core.Status()); return; }
            if (!Delve.Core.IsServer) { SdtdConsole.Instance.Output("Run on the host/server."); return; }
            if (action == "verify") { SdtdConsole.Instance.Output(Delve.Core.VerifyDefinitions()); return; }
            if (action == "save") { Delve.Core.Save(); SdtdConsole.Instance.Output("Delve save requested; inspect log if state is unavailable."); return; }
            if (action == "boss" || action == "patrol")
            {
                World world = GameManager.Instance.World;
                EntityPlayer p = null;
                int id;
                if (args.Count > 1 && int.TryParse(args[1], out id)) p = world.GetEntity(id) as EntityPlayer;
                else if (senderInfo.RemoteClientInfo != null) p = world.GetEntity(senderInfo.RemoteClientInfo.entityId) as EntityPlayer;
                else p = world.GetPrimaryPlayer();
                SdtdConsole.Instance.Output(action == "boss" ? Delve.Core.SpawnBoss(p,true) : Delve.Core.SpawnPatrol(p)); return;
            }
            SdtdConsole.Instance.Output(getDescription());
        }
        catch (Exception ex) { Log.Error("[Delve] Command failed: " + ex); SdtdConsole.Instance.Output("Delve command failed; see log."); }
    }
}

