using System;
using System.Reflection;
using HarmonyLib;
namespace DelveTomeTrading {
 public class ModApi:IModApi {
  public void InitMod(Mod mod){new Harmony("delve.tome.trading").PatchAll(Assembly.GetExecutingAssembly());}
 }
 public static class Tomes {
  public static bool IsTome(string name){switch(name){
   case "delveLessonFarmingNotes":case "delveLessonCookingNotes":case "delveLessonMiningNotes":
   case "delveLessonSmithingNotes":case "delveLessonCarpentryNotes":case "delveLessonAlchemyNotes":return true;
   default:return false;
  }}
 }
 // A fixed lesson fee, independent of trader markup, barter perks or discounts.
 // Native purchase UI and payment both use GetBuyPrice; other items are untouched.
 [HarmonyPatch(typeof(XUiM_Trader),"GetBuyPrice")]
 public static class TomePrice {
  static bool Prefix(ItemValue __1,int __2,ItemClass __3,ref int __result){
   var item=__3??(__1==null?null:__1.ItemClass);
   if(item==null || !Tomes.IsTome(item.GetItemName()))return true;
   __result=checked(500*Math.Max(0,__2));return false;
  }
 }
}
