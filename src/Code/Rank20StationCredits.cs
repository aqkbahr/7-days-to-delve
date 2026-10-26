using System;using System.Collections.Generic;using System.IO;using System.Reflection.Emit;using System.Runtime.CompilerServices;using HarmonyLib;
namespace Delve {
 // Whole saved fuel units become output only after a job actually completes.
 // Fractions belong to the workstation and survive job changes and save/reload.
 public static class Rank20StationCredits {
  public const byte Version=201;
  public sealed class Credit {public float Fuel,Extraction;public bool Extended;}
  public static readonly ConditionalWeakTable<TileEntityWorkstation,Credit> Data=new ConditionalWeakTable<TileEntityWorkstation,Credit>();
  public static byte ReadVersion(byte version,TileEntityWorkstation station){Data.GetOrCreateValue(station).Extended=version==Version;return version==Version?(byte)50:version;}
  public static void Complete(TileEntityWorkstation station,RecipeQueueItem job){
   if(job==null||job.Recipe==null||job.Recipe.IsScrap)return;var snapshot=CraftedProperties.Data.GetOrCreateValue(job);var credit=Data.GetOrCreateValue(station);
   if(Rank20Crafting.Extracts(job.Recipe)&&(snapshot.Flags&Rank20Crafting.Extraction)!=0)credit.Extraction=snapshot.PreparedCarry;
   if((snapshot.Flags&Rank20Crafting.Smelting)!=0&&TrainingHooks.CraftedSkill(job.Recipe.GetName(),job.Recipe.craftingArea)=="Smithing")foreach(var ingredient in job.Recipe.ingredients)if(ingredient.itemValue.ItemClass.GetItemName()=="delveCharcoal")credit.Fuel+=ingredient.count*.15f;
   station.setModified();Pay(station);
  }
  public static void Pay(TileEntityWorkstation station){
   var credit=Data.GetOrCreateValue(station);int due=(int)Math.Floor(credit.Fuel+.00001f);if(due<1||station.Output==null)return;
   var item=ItemClass.GetItem("delveCharcoal",false);if(item==null||item.type==0)return;
   // One unit at a time avoids a partial insertion followed by a full refund.
   int cap=Math.Min(due,64);for(int i=0;i<cap;i++){if(ItemStack.AddToItemStackArray(station.Output,new ItemStack(item.Clone(),1),-1)<0)break;credit.Fuel-=1;station.setModified();}
  }
 }
 [HarmonyPatch(typeof(TileEntityWorkstation),"write")]
 public static class WriteStationCredits {
  static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> input){bool found=false;foreach(var code in input){if(!found&&code.LoadsConstant(50)){code.opcode=OpCodes.Ldc_I4;code.operand=(int)Rank20StationCredits.Version;found=true;}yield return code;}if(!found)throw new InvalidOperationException("Workstation serialization version changed");}
  static void Postfix(TileEntityWorkstation __instance,PooledBinaryWriter __0){var c=Rank20StationCredits.Data.GetOrCreateValue(__instance);__0.Write(c.Fuel);__0.Write(c.Extraction);}
 }
 [HarmonyPatch(typeof(TileEntityWorkstation),"read")]
 public static class ReadStationCredits {
  static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> input){bool found=false;foreach(var code in input){yield return code;if(!found&&code.Calls(AccessTools.Method(typeof(BinaryReader),"ReadByte"))){yield return new CodeInstruction(OpCodes.Ldarg_0);yield return new CodeInstruction(OpCodes.Call,AccessTools.Method(typeof(Rank20StationCredits),"ReadVersion"));found=true;}}if(!found)throw new InvalidOperationException("Workstation read version changed");}
  static void Postfix(TileEntityWorkstation __instance,PooledBinaryReader __0){var c=Rank20StationCredits.Data.GetOrCreateValue(__instance);c.Fuel=c.Extended?__0.ReadSingle():0;c.Extraction=c.Extended?__0.ReadSingle():0;if(float.IsNaN(c.Fuel)||float.IsInfinity(c.Fuel)||c.Fuel<-.0001f||float.IsNaN(c.Extraction)||c.Extraction<-.0001f||c.Extraction>=1.0001f)throw new InvalidDataException("Invalid workstation maker credit");}
 }
 [HarmonyPatch(typeof(TileEntityWorkstation),"UpdateTick")]
 public static class PayStationCredits {static void Postfix(TileEntityWorkstation __instance,World __0){if(!__0.IsRemote())Rank20StationCredits.Pay(__instance);}}
}
