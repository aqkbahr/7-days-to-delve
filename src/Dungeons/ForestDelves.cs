using HarmonyLib;

public class ForestDelves : IModApi
{
    public void InitMod(Mod mod){new Harmony("delve.forestdelves").PatchAll(typeof(ForestDelves).Assembly);}
}

// Run after the existing starter-board cap. The original ten-contract campaign
// remains Tier 1; its existing synchronized milestone opens the Tier 2 board.
[HarmonyPatch(typeof(EntityTrader),"PopulateActiveQuests")]
public class ForestDelveBoardTier
{
    [HarmonyPriority(Priority.Last)]
    static void Prefix(EntityTrader __instance,EntityPlayer __0,ref int __1)
    {
        if(EntityClass.GetEntityClassName(__instance.entityClass)=="delveWayrestSteward")
            __1=__0!=null && __0.Buffs.GetCustomVar("delveWayrestReady")>=1?2:1;
    }
}

// Replace one guardian slot in the deepest native encounter volume. Preserve
// native counts, activation, pose compatibility and quest-clear bookkeeping.
[HarmonyPatch(typeof(SleeperVolume),"Spawn")]
public class ForestDelveGuardian
{
    static void Prefix(SleeperVolume __instance,World __0,ref int __1,BlockSleeper __3,int ___numSpawned)
    {
        if(__0==null||__0.IsRemote()||___numSpawned!=0||__instance.PrefabInstance==null)return;
        var poi=__instance.PrefabInstance;string name=poi.prefab.PrefabName;int volume;string enemy;
        if(name=="delve_dungeon_cave_06"){volume=2;enemy="delveCorruptedWalker";}
        else if(name=="delve_dungeon_cave_11"){volume=0;enemy="delveCorruptedWalker";}
        else if(name=="delve_dungeon_cemetery_02"||name=="delve_dungeon_cave_12"){volume=2;enemy="delvePossessedSoldier";}
        else return;
        if(poi.sleeperVolumes==null||poi.sleeperVolumes.IndexOf(__instance)!=volume)return;
        int id=EntityClass.FromString(enemy);EntityClass definition;
        if(!EntityClass.list.TryGetValue(id,out definition))return;
        if(__3!=null&&__3.ExcludesWalkType(EntityAlive.GetSpawnWalkType(definition)))return;
        __1=id;
    }
}
