using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Xml;
using UnityEngine;
public class ConsoleCmdStationProgression:ConsoleCmdAbstract {
 public override string[] getCommands(){return new[]{"stationverify"};}
 public override string getDescription(){return "Verify frozen crafting split, native station menus, gates and queue output.";}
 static int checks;
 static void Check(bool value,string message){checks++;if(!value)throw new Exception(message);}
 public override void Execute(List<string> args,CommandSenderInfo sender){
  EntityPlayer player=null;bool oldWorkstation=XUiM_Recipes.WorkstationCrafting;var oldBackpack=XUiM_Recipes.BackpackCrafting;
  try{
   checks=0;XUiM_Recipes.WorkstationCrafting=true;XUiM_Recipes.BackpackCrafting=(BackpackCraftingOptions)1;
   var core=Delve.Core.VerifyDefinitions();Check(core.StartsWith("PASS:"),core);SdtdConsole.Instance.Output(core);
   player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),Vector3.zero) as EntityPlayer;player.world=GameManager.Instance.World;player.Progression.Level=1;
   foreach(string iron in new[]{"oreIronBoulder","terrOreIron"}){
    bool lead=false;foreach(var drop in Block.GetBlockValue(iron,false).Block.itemsToDrop[EnumDropEvent.Harvest])if(drop.name=="resourceScrapLead" && drop.minCount==5)lead=true;
    Check(lead,"Early lead harvest source "+iron);
   }
   var doc=new XmlDocument();doc.Load(Path.Combine(ModManager.GetMod("StationProbe",true).Path,"slice-checks.xml"));
   var all=CraftingManager.GetAllRecipes();var live=new Dictionary<string,Recipe>();
   foreach(var r in all)if(!r.IsScrap && (Delve.ForestSliceCatalog.Rank(r)<=20 || (r.GetName()=="thrownDynamite" && Delve.ForestSliceCatalog.Rank(r)==40)))live.Add(Delve.ForestSliceCatalog.Key(r),r);
   var backpack=XUiM_Recipes.FilterRecipesByWorkstation("",all);int count=0,queues=0;
   foreach(XmlElement row in doc.SelectNodes("/slice/recipe")){
    Recipe r;Check(live.TryGetValue(row.GetAttribute("key"),out r),"Missing variant "+row.GetAttribute("key"));
    string skill=row.GetAttribute("skill"),station=row.GetAttribute("station");int rank=int.Parse(row.GetAttribute("rank"));
    foreach(string s in new[]{"Farming","Cooking","Mining","Smithing","Carpentry","Alchemy"})Delve.CharacterProgression.Set(player,"delvePractice"+s,Delve.ProficiencyRules.Threshold(rank));
    Check(Delve.ForestSliceCatalog.Rank(r)==rank,"Wrong gate "+r.GetName());
    Check((Delve.TrainingHooks.CraftedSkill(r.GetName(),r.craftingArea)??"")==skill,"Wrong practice "+r.GetName());
    Check(r.IsUnlocked(player) && r.CanCraft(new List<ItemStack>(r.ingredients),player,-1),"Not available at declared stage "+r.GetName());
    Check(!r.CanCraft(new List<ItemStack>(),player,-1),"No-input craft "+r.GetName());
    Check(backpack.Contains(r)==(station==""),"Wrong native inventory menu "+r.GetName());
    if(rank>1 && skill!=""){
     Delve.CharacterProgression.Set(player,"delvePractice"+skill,Delve.ProficiencyRules.Threshold(rank-1));
     Check(!r.IsUnlocked(player) && !r.CanCraft(new List<ItemStack>(r.ingredients),player,-1),"Lower rank bypass "+r.GetName());
     Delve.CharacterProgression.Set(player,"delvePractice"+skill,Delve.ProficiencyRules.Threshold(rank));
    }
    if(station!=""){
     Check(XUiM_Recipes.FilterRecipesByWorkstation(station,all).Contains(r),"Station menu missing "+r.GetName()+" @ "+station);
     var te=new TileEntityWorkstation((Chunk)null);te.SetDisableModifiedCheck(true);
     te.Queue=new[]{new RecipeQueueItem{Recipe=r,Multiplier=1,CraftingTimeLeft=0,OneItemCraftTime=1,Quality=1,StartingEntityId=-1}};
     typeof(TileEntityWorkstation).GetMethod("HandleRecipeQueue",BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic).Invoke(te,new object[]{2f});
     int output=0;foreach(var stack in te.Output)if(stack.itemValue.type==r.itemValueType)output+=stack.count;
     Check(output==r.count,"Queue output mismatch "+r.GetName());queues++;
    }
    count++;
   }
   Check(count==live.Count,"Uncatalogued recipe exposed");
   foreach(XmlElement station in doc.SelectNodes("/slice/station")){
    string name=station.GetAttribute("name"),family=station.GetAttribute("family");int tier=int.Parse(station.GetAttribute("tier"));
    Check(Block.GetBlockValue(name,false).Block is BlockWorkstation,"Non-workstation "+name);
    Check(CraftingManager.GetWorkstationData(name).WorkstationWindow=="workstation_"+family,"Wrong native station window "+name);
    var menu=XUiM_Recipes.FilterRecipesByWorkstation(name,all);
    foreach(var r in live.Values){
     string area=r.craftingArea??"";
     bool expected=area==family || (tier>=2 && area==family+"Tier2") || (tier>=3 && area==family+"Tier3");
     Check(menu.Contains(r)==expected,"Tier/wrong-station bypass "+name+" / "+r.GetName());
    }
   }
   foreach(var r in all)if(!r.IsScrap && Delve.ForestSliceCatalog.Rank(r)>20)Check(!Delve.RecipeProgression.Allowed(r,player),"Later recipe leaked "+r.GetName());
   SdtdConsole.Instance.Output("[StationProgression] PASS "+checks+" native checks; "+count+" exact variants, "+queues+" station queue outputs, 21 station menus, inventory exclusion, prior-tier inclusion, rank boundaries, practice ownership and later-content exclusion.");
  }catch(Exception e){SdtdConsole.Instance.Output("[StationProgression] FAIL "+e);}
  finally{XUiM_Recipes.WorkstationCrafting=oldWorkstation;XUiM_Recipes.BackpackCrafting=oldBackpack;if(player!=null)UnityEngine.Object.Destroy(player.gameObject);}
 }
}
