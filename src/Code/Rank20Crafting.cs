using System;using HarmonyLib;
namespace Delve {
 public static class Rank20Crafting {
  public static bool Construction(Recipe recipe){if(recipe==null||recipe.IsScrap)return false;switch(recipe.GetName()){case "woodLogPillar100":case "frameShapes":case "frameShapes:VariantHelper":case "woodShapes":case "woodBlock":case "ladderWood":case "oldWoodDoor":case "woodHatch":case "woodDoor1":case "woodHatch1":case "cntWoodWritableCrate":return true;default:return false;}}
  public const uint Hearty=256,Trail=512,Lasting=1024,Honed=2048,Plates=4096,Bowyer=8192,Dressings=16384,Brews=32768,Extraction=65536,Smelting=131072;
  public static uint Capture(EntityAlive p){uint flags=0;string[] skills={"Cooking","Cooking","Cooking","Smithing","Smithing","Carpentry","Alchemy","Alchemy","Alchemy","Smithing"};string[] perks={"HeartyPortions","TrailRations","LastingMeals","HonedEdge","ReinforcedPlates","Bowyer","CleanDressings","PotentBrews","CleanExtraction","EfficientSmelting"};uint[] bits={Hearty,Trail,Lasting,Honed,Plates,Bowyer,Dressings,Brews,Extraction,Smelting};for(int i=0;i<bits.Length;i++)if(Rank20.Has(p,skills[i],perks[i]))flags|=bits[i];return flags;}
  public static bool Marked(ItemValue item,uint flag){int value;return item!=null&&item.TryGetMetadata("delveMakerTraits",out value)&&((uint)value&flag)!=0;}
  public static bool Preserved(string n){return n=="foodDelveTrailRations"||n=="foodDelveTrailRation"||n=="foodDelveTravelBread"||n=="foodDelveBerryPreserve"||n=="foodDelveHoneyberryCakes";}
  public static bool Extracts(Recipe r){if(r==null||r.IsScrap||r.ingredients==null||r.ingredients.Count==0)return false;string n=r.GetName();if(n!="delveHerbalExtract"&&n!="delveEmberSalts")return false;foreach(var i in r.ingredients){string raw=i.itemValue.ItemClass.GetItemName();if(raw=="resourceDelveYarrow"||raw=="resourceDelveThyme"||raw=="resourceDelveMooncap")return true;}return false;}
  public static void Stamp(ItemValue item,Recipe recipe,uint flags){
   if(item==null||item.ItemClass==null||recipe==null||recipe.IsScrap)return;string name=item.ItemClass.GetItemName(),skill=TrainingHooks.CraftedSkill(name,recipe.craftingArea);uint traits=0;
   if(skill=="Cooking"){
    if(name.StartsWith("food",StringComparison.Ordinal))traits|=flags&Hearty;
    traits|=flags&Lasting;
    if((flags&Trail)!=0&&Preserved(name)){var packed=ItemClass.GetItem(name+"DelvePacked");if(packed!=null&&packed.type>0){item.type=packed.type;traits|=Trail;}}
   }
   string material=item.ItemClass.MadeOfMaterial==null?"":item.ItemClass.MadeOfMaterial.id.ToLowerInvariant();bool metal=material.Contains("iron")||material.Contains("steel")||material.Contains("metal");
   if(skill=="Smithing"&&metal){if(Rank20.Skill(item)!=null)traits|=flags&Honed;if(item.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse("heavyArmor")))traits|=flags&Plates;}
   if(skill=="Carpentry"&&Rank20.Skill(item)=="Archery")traits|=flags&Bowyer;
   if(skill=="Alchemy"){
    if(item.ItemClass.HasAnyTags(FastTags<TagGroup.Global>.Parse("medical,medicalSkill")))traits|=flags&Dressings;
    if(name=="delveLesserHealingPotion"||name=="delveLesserStaminaPotion")traits|=flags&Brews;
   }
   if(traits!=0)item.SetMetadata("delveMakerTraits",(int)traits);
  }
  public static int OutputCount(ItemValue item,int count,TileEntityWorkstation station){
   if(station==null||station.Queue==null||station.Queue.Length==0)return count;var job=station.Queue[station.Queue.Length-1];if(job==null||!Extracts(job.Recipe))return count;var data=CraftedProperties.Data.GetOrCreateValue(job);float carry=Rank20StationCredits.Data.GetOrCreateValue(station).Extraction;int result=(data.Flags&Extraction)!=0?Rank20Rules.BonusOutput(count,.15f,ref carry):count;data.PreparedCarry=carry;return result;
  }
  public static float ConsumptionBonus(ItemValue item,string stat){
   if(item==null)return 0;float bonus=0;
   if(stat=="$foodAmountAdd"&&Marked(item,Hearty))bonus+=.15f;
   if(stat=="medicalRegHealthAmount"&&Marked(item,Dressings))bonus+=.15f;
   return bonus;
  }
 }
 [HarmonyPatch(typeof(EffectManager),"GetValue")]
 public static class Rank20ConstructionCost {
  static void Postfix(PassiveEffects __0,EntityAlive __3,Recipe __4,FastTags<TagGroup.Global> __5,ref float __result){
   if(__0==PassiveEffects.CraftingIngredientCount&&__result>0&&Rank20Crafting.Construction(__4)&&__5.Test_AnySet(FastTags<TagGroup.Global>.Parse("resourceWood"))&&Rank20.Has(__3,"Carpentry","EfficientFraming"))__result=Math.Max(1,(float)Math.Ceiling(__result*.9f-.00001f));
  }
 }
 [HarmonyPatch(typeof(TileEntityWorkstation),"AddCraftComplete")]
 public static class Rank20CommitExtraction {
  static void Postfix(TileEntityWorkstation __instance){
   if(CraftedProperties.Station!=__instance||__instance.Queue==null||__instance.Queue.Length==0)return;
   var job=__instance.Queue[__instance.Queue.Length-1];Rank20StationCredits.Complete(__instance,job);
  }
 }
 [HarmonyPatch(typeof(EffectManager),"GetValue")]
 public static class Rank20MakerDamage {static void Postfix(PassiveEffects __0,ItemValue __1,ref float __result){if(__0==PassiveEffects.EntityDamage&&__1!=null&&(Rank20Crafting.Marked(__1,Rank20Crafting.Honed)||Rank20Crafting.Marked(__1,Rank20Crafting.Bowyer)))__result*=1.05f;}}
 [HarmonyPatch(typeof(ItemValue),"ModifyValue")]
 public static class Rank20MakerArmor {
  static void Prefix(float __3,out float __state){__state=__3;}
  static void Postfix(ItemValue __instance,PassiveEffects __2,ref float __3,float __state){if(__2==PassiveEffects.PhysicalDamageResist&&Rank20Crafting.Marked(__instance,Rank20Crafting.Plates)&&__3>__state)__3+=.1f*(__3-__state);}
 }
 [HarmonyPatch(typeof(MinEventActionAddBuff),"Execute")]
 public static class Rank20MealContext {
  [ThreadStatic]public static ItemValue Item;
  static void Prefix(MinEventParams __0,out ItemValue __state){__state=Item;Item=__0==null?null:__0.ItemValue;}
  static Exception Finalizer(Exception __exception,ItemValue __state){Item=__state;return __exception;}
 }
 [HarmonyPatch(typeof(EntityBuffs),"AddBuff",new Type[]{typeof(string),typeof(int),typeof(bool),typeof(bool),typeof(float)})]
 public static class Rank20MealDuration {
  static void Prefix(string __0,ref float __4){if((__0=="delveForestMeal"||__0=="delveForestDrink")&&Rank20Crafting.Marked(Rank20MealContext.Item,Rank20Crafting.Lasting)){var buff=BuffManager.GetBuff(__0);if(buff!=null)__4=(__4>0?__4:buff.DurationMax)*1.15f;}}
 }
 [HarmonyPatch(typeof(XUiM_Recipes),"GetRecipeCraftTime")]
 public static class Rank20ProcessingSpeed {
  static void Postfix(XUi __0,Recipe __1,ref float __result){if(__0==null||__1==null||__1.IsScrap)return;var p=__0.playerUI.entityPlayer;string name=__1.GetName();
   if(__1.craftingArea=="delveSortingTable"&&Rank20.Has(p,"Mining","SortingTable")&&(name=="delveIronConcentrate"||name=="delveDressedStone"||name=="resourceCrushedSand"||name=="resourceCobblestones"))__result/=1.2f;
   if(Rank20.Has(p,"Carpentry","TannerandWeaver")&&(name=="delveCuredLeather"||name=="delveWovenCloth"||name=="resourceCloth"||name=="resourceLeather"))__result/=1.2f;
  }
 }
}

