using System;
using System.Collections.Generic;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using HarmonyLib;
namespace Delve
{
    // Queued jobs snapshot their maker's perks. The versioned queue extension
    // travels with workstation network/save data, including offline completion.
    public static class CraftedProperties
    {
        public const ushort QueueVersion=53506;
        public sealed class Snapshot {public uint Flags;public float YieldCarry,PreparedCarry;}
        public static readonly ConditionalWeakTable<object,Snapshot> Data=new ConditionalWeakTable<object,Snapshot>();
        public static readonly ConditionalWeakTable<XUi,Restore> Restoring=new ConditionalWeakTable<XUi,Restore>();
        public sealed class Restore {public RecipeQueueItem[] Queue;}
        [ThreadStatic]public static Snapshot Pending;
        [ThreadStatic]public static TileEntityWorkstation Station;
        public static uint Capture(EntityAlive p)
        {return (uint)(128|(p!=null && ProgressionRuntime.Has(p,"Cooking","NourishingRecipes")?1:0)|(p!=null && ProgressionRuntime.Has(p,"Smithing","SoundMetalwork")?2:0))|Rank20Crafting.Capture(p);}
        public static void Copy(object from,object to){var a=Data.GetOrCreateValue(from);var b=Data.GetOrCreateValue(to);b.Flags=a.Flags;b.YieldCarry=a.YieldCarry;}
        public static void Transfer(XUiC_RecipeStack[] ui,RecipeQueueItem[] queue)
        {if(ui==null || queue==null)return;for(int i=0;i<Math.Min(ui.Length,queue.Length);i++)if(ui[i]!=null && queue[i]!=null)Copy(ui[i],queue[i]);}
        public static void Stamp(ItemValue item,Recipe recipe,uint flags)
        {
            if(item==null || item.ItemClass==null || recipe==null || recipe.IsScrap)return;
            string name=item.ItemClass.GetItemName(),skill=TrainingHooks.CraftedSkill(name,recipe.craftingArea);
            Rank20Crafting.Stamp(item,recipe,flags);
            if((flags&1)!=0 && skill=="Cooking")item.SetMetadata("delveNourishment",1);
            if((flags&2)!=0 && skill=="Smithing" && item.MaxUseTimes>0 && item.ItemClass.MadeOfMaterial!=null)
            {
                string material=item.ItemClass.MadeOfMaterial.id.ToLowerInvariant();
                if(material.Contains("iron") || material.Contains("steel") || material.Contains("metal"))item.SetMetadata("delveMetalwork",1);
            }
        }
        public static void StampUI(XUiC_RecipeStack stack)
        {
            var t=Traverse.Create(stack);var original=t.Field<ItemValue>("originalItem").Value;
            if(original!=null && !original.IsEmpty())return;
            Stamp(t.Field<ItemValue>("outputItemValue").Value,stack.GetRecipe(),Data.GetOrCreateValue(stack).Flags);
        }
        public static ItemStack StationOutput(ItemValue item,int count)
        {
            if(Station!=null && Station.Queue!=null && Station.Queue.Length>0)
            {var job=Station.Queue[Station.Queue.Length-1];if(job!=null)Stamp(item,job.Recipe,Data.GetOrCreateValue(job).Flags);}
            return new ItemStack(item,Rank20Crafting.OutputCount(item,count,Station));
        }
    }
    [HarmonyPatch(typeof(XUiC_CraftingQueue),"AddRecipeToCraftAtIndex")]
    public static class RestoreCraftSnapshot
    {
        static void Prefix(XUiC_CraftingQueue __instance,int __0,int __7,out CraftedProperties.Snapshot __state)
        {
            __state=CraftedProperties.Pending;CraftedProperties.Pending=null;CraftedProperties.Restore restore;
            if(__7>=0 && CraftedProperties.Restoring.TryGetValue(__instance.xui,out restore) && restore.Queue!=null && __0>=0 && __0<restore.Queue.Length && restore.Queue[__0]!=null)
                CraftedProperties.Pending=CraftedProperties.Data.GetOrCreateValue(restore.Queue[__0]);
        }
        static Exception Finalizer(Exception __exception,CraftedProperties.Snapshot __state){CraftedProperties.Pending=__state;return __exception;}
    }
    [HarmonyPatch(typeof(XUiC_RecipeStack),"SetRecipe")]
    public static class CaptureCraftSnapshot
    {
        static void Prefix(XUiC_RecipeStack __instance,int __5,out CraftedProperties.Snapshot __state)
        {__state=CraftedProperties.Pending??new CraftedProperties.Snapshot{Flags=__5<0?CraftedProperties.Capture(__instance.xui.playerUI.entityPlayer):128u};}
        static void Postfix(XUiC_RecipeStack __instance,CraftedProperties.Snapshot __state,bool __result)
        {
            if(!__result)return;
            var data=CraftedProperties.Data.GetOrCreateValue(__instance);data.Flags=__state.Flags;data.YieldCarry=__state.YieldCarry;
        }
    }
    [HarmonyPatch(typeof(XUiC_RecipeStack),"CopyTo")]
    public static class MoveCraftSnapshot
    {static void Postfix(XUiC_RecipeStack __instance,XUiC_RecipeStack __0){CraftedProperties.Copy(__instance,__0);}}
    [HarmonyPatch(typeof(XUi),"SetCraftingData")]
    public static class RestoreBackpackCrafting
    {static void Prefix(XUi __instance,CraftingData __0){CraftedProperties.Restoring.GetOrCreateValue(__instance).Queue=__0==null?null:__0.RecipeQueueItems;}}
    [HarmonyPatch(typeof(XUi),"GetCraftingData")]
    public static class SaveBackpackCrafting
    {static void Postfix(XUi __instance,CraftingData __result){var group=__instance.FindWindowGroupByName("crafting");var q=group==null?null:group.GetChildByType<XUiC_CraftingQueue>();if(q!=null && __result!=null)CraftedProperties.Transfer(q.GetRecipesToCraft(),__result.RecipeQueueItems);}}
    [HarmonyPatch(typeof(XUiC_WorkstationWindowGroup),"OnOpen")]
    public static class RestoreStationCrafting
    {
        static void Prefix(XUiC_WorkstationWindowGroup __instance){CraftedProperties.Restoring.GetOrCreateValue(__instance.xui).Queue=__instance.WorkstationData.GetRecipeQueueItems();}
        static void Postfix(XUiC_WorkstationWindowGroup __instance){CraftedProperties.Restoring.Remove(__instance.xui);}
    }
    [HarmonyPatch(typeof(XUiC_WorkstationWindowGroup),"syncTEfromUI")]
    public static class SaveStationCrafting
    {static void Postfix(XUiC_WorkstationWindowGroup __instance){var q=__instance.GetChildByType<XUiC_CraftingQueue>();if(q!=null)CraftedProperties.Transfer(q.GetRecipesToCraft(),__instance.WorkstationData.GetRecipeQueueItems());}}
    [HarmonyPatch(typeof(RecipeQueueItem),"Write")]
    public static class WriteCraftSnapshot
    {
        static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> input)
        {
            bool changed=false;foreach(var code in input){if(!changed && code.opcode==OpCodes.Ldc_I4_2){code.opcode=OpCodes.Ldc_I4;code.operand=(int)CraftedProperties.QueueVersion;changed=true;}yield return code;}
            if(!changed)throw new InvalidOperationException("Craft queue serialization version marker changed.");
        }
        static void Postfix(RecipeQueueItem __instance,PooledBinaryWriter __0){var data=CraftedProperties.Data.GetOrCreateValue(__instance);__0.Write(data.Flags);__0.Write(data.YieldCarry);}
    }
    [HarmonyPatch(typeof(RecipeQueueItem),"Read")]
    public static class ReadCraftSnapshot
    {
        static void Prefix(PooledBinaryReader __0,out ushort __state)
        {long position=__0.BaseStream.Position;__state=__0.ReadUInt16();__0.BaseStream.Position=position;}
        static void Postfix(RecipeQueueItem __instance,PooledBinaryReader __0,ushort __state)
        {var data=CraftedProperties.Data.GetOrCreateValue(__instance);data.Flags=__state==CraftedProperties.QueueVersion?__0.ReadUInt32():__state==53505?__0.ReadByte():128u;data.YieldCarry=__state==CraftedProperties.QueueVersion?__0.ReadSingle():0;}
    }
    [HarmonyPatch(typeof(XUiC_RecipeStack),"outputStack")]
    public static class StampCraftOutput
    {
        static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> input)
        {
            int count=0;foreach(var code in input)
            {
                yield return code;
                if(code.opcode==OpCodes.Stfld && Equals(code.operand,AccessTools.Field(typeof(XUiC_RecipeStack),"outputItemValue")))
                {yield return new CodeInstruction(OpCodes.Ldarg_0);yield return new CodeInstruction(OpCodes.Call,AccessTools.Method(typeof(CraftedProperties),"StampUI"));count++;}
            }
            if(count==0)throw new InvalidOperationException("Craft output creation hook changed.");
        }
    }
    [HarmonyPatch(typeof(TileEntityWorkstation),"HandleRecipeQueue")]
    public static class StampOfflineCraftOutput
    {
        static void Prefix(TileEntityWorkstation __instance,out TileEntityWorkstation __state){__state=CraftedProperties.Station;CraftedProperties.Station=__instance;}
        static Exception Finalizer(Exception __exception,TileEntityWorkstation __state){CraftedProperties.Station=__state;return __exception;}
        static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> input)
        {
            int count=0;foreach(var code in input)
            {
                if(code.opcode==OpCodes.Newobj && Equals(code.operand,AccessTools.Constructor(typeof(ItemStack),new[]{typeof(ItemValue),typeof(int)})))
                {code.opcode=OpCodes.Call;code.operand=AccessTools.Method(typeof(CraftedProperties),"StationOutput");count++;}yield return code;
            }
            if(count!=1)throw new InvalidOperationException("Station output creation hook changed.");
        }
    }
    [HarmonyPatch(typeof(EffectManager),"GetValue")]
    public static class CraftedDurability
    {static void Postfix(PassiveEffects __0,ItemValue __1,ref float __result){int marker;if(__0==PassiveEffects.DegradationMax && __1!=null && __1.TryGetMetadata("delveMetalwork",out marker) && marker==1)__result*=1.15f;}}
    [HarmonyPatch(typeof(MinEventActionModifyCVar),"Execute")]
    public static class CraftedNutrition
    {
        static void Prefix(MinEventActionModifyCVar __instance,MinEventParams __0,CVarOperation ___operation,out float __state)
        {
            // 3.4 exposes value/cvarRef as properties rather than fields. A
            // failed field-injection patch aborts core startup, including the
            // workstation serialization patches required by existing saves.
            __state=__instance.value;if(__0==null||__0.ItemValue==null||__instance.cvarRef||__instance.value<=0||___operation!=CVarOperation.add)return;
            int marker;float bonus=Rank20Crafting.ConsumptionBonus(__0.ItemValue,__instance.cvarName);
            if((__instance.cvarName=="$foodAmountAdd"||__instance.cvarName=="$waterAmountAdd")&&__0.ItemValue.TryGetMetadata("delveNourishment",out marker)&&marker==1)bonus+=.1f;
            if(__instance.cvarName.EndsWith("Duration",StringComparison.Ordinal)&&Rank20Crafting.Marked(__0.ItemValue,Rank20Crafting.Lasting))bonus+=.15f;
            __instance.value*=1+bonus;
        }
        static Exception Finalizer(Exception __exception,MinEventActionModifyCVar __instance,float __state){__instance.value=__state;return __exception;}
    }
}


