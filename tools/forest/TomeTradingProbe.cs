using System;
using System.Collections.Generic;
public class ConsoleCmdTomeTrading:ConsoleCmdAbstract {
 public override string[] getCommands(){return new[]{"tomeverify"};}
 public override string getDescription(){return "Check optional tome recipes, exact prices and native vendor restocks.";}
 public override void Execute(List<string> args,CommandSenderInfo sender){try{
  string[] skills={"Farming","Cooking","Mining","Smithing","Carpentry","Alchemy"};
  foreach(var skill in skills){
   var name="delveLesson"+skill+"Notes";var item=ItemClass.GetItem(name,false);
   if(item.IsEmpty())throw new Exception("Missing tome "+name);
   if(CraftingManager.GetRecipe(name)!=null)throw new Exception("Craftable tome "+name);
   foreach(int count in new[]{1,2,3})if(XUiM_Trader.GetBuyPrice(null,item,count,item.ItemClass,-1)!=500*count)throw new Exception("Wrong purchase price "+name);
  }
  int vendors=0,cycles=0;var found=new HashSet<string>();var rng=new GameRandom();rng.SetSeed(51973);
  foreach(var info in TraderInfo.traderInfoList){
   if(info==null || info.IsVendingMachine || info.PlayerOwned || info.Rentable)continue;
   vendors++;
   for(int i=0;i<100;i++){
    var distinct=new HashSet<string>();
    foreach(var stack in info.Spawn(rng))if(stack.count>0 && DelveTomeTrading.Tomes.IsTome(stack.itemValue.ItemClass.GetItemName()))distinct.Add(stack.itemValue.ItemClass.GetItemName());
    if(distinct.Count<3)throw new Exception("Vendor "+info.Id+" restock "+i+" has "+distinct.Count+" tome types");
    foreach(var n in distinct)found.Add(n);cycles++;
   }
  }
  if(vendors==0 || found.Count!=6)throw new Exception("Missing vendor/tome coverage: vendors="+vendors+", types="+found.Count);
  SdtdConsole.Instance.Output("[Tomes] PASS six noncraftable tomes, exact500 gold (1/2/3 quantities), "+cycles+" native restocks across "+vendors+" vendors with >=3 distinct types; allsix offered.");
 }catch(Exception e){SdtdConsole.Instance.Output("[Tomes] FAIL "+e);}}
}
