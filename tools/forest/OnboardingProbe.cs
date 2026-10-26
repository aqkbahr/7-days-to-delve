using System;using System.Collections.Generic;using System.Reflection;using Delve;using UnityEngine;
public class ConsoleCmdOnboardingProbe:ConsoleCmdAbstract {
 public override string[] getCommands(){return new[]{"onboardingverify"};}
 public override string getDescription(){return "Disposable onboarding and early perk access checks";}
 int checks;void Check(bool ok,string why){checks++;if(!ok)throw new Exception(why);}
 public override void Execute(List<string> args,CommandSenderInfo sender){try{
  checks=0;int early=0;var reachable=new HashSet<string>();bool changed;
  do{changed=false;foreach(var pair in TalentCatalog.Entries){if(!pair.Value.Implemented||reachable.Contains(pair.Key))continue;if(pair.Value.CanBuy(99,false,false,k=>reachable.Contains(k))){reachable.Add(pair.Key);changed=true;}}}while(changed);
  foreach(var pair in TalentCatalog.Entries){if(pair.Value.Rank<=20){Check(reachable.Contains(pair.Key),"early prerequisite "+pair.Key);early++;}if(pair.Value.Implemented)Check(reachable.Contains(pair.Key),"stranded implementation "+pair.Key);}
  Check(early==100,"all hundred early choices");
  foreach(string skill in new[]{"Farming","Cooking","Mining","Smithing","Carpentry","Alchemy"}){
   string id="delveLesson"+skill;Check(QuestClass.CreateQuest(id)!=null,"lesson registered "+id);Check(CraftingManager.GetRecipe(id+"Notes")==null,"tomes vendor-only "+id);
  }
  foreach(string id in new[]{"delveArrival","delveHearth","delveSupplyLesson","delveEmbers","delveArborPreparation"})Check(QuestClass.CreateQuest(id)!=null,"preparation chain "+id);
  foreach(string weapon in new[]{"delveBoneDagger","delveOakCudgel","delveAshSpear","delveLeatherKnuckles","delveBorderBow","delveStarterWand","delveStarterStaff","delveStarterTotem","delveMendingTotem"}){
   var quest=QuestClass.CreateQuest("delveArrival");ObjectiveCraft objective=null;foreach(var o in quest.Objectives)if(o is ObjectiveCraft&&o.ID=="delveBoneDagger")objective=(ObjectiveCraft)o;
   Check(objective!=null,"weapon objective exists");objective.OwnerQuest=quest;objective.SetupObjective();objective.SetupDisplay();Check(objective.Description.Contains("any starter weapon"),"choice label: quest="+quest.ID+" objective="+objective.ID+" text="+objective.Description);
   var source=new ItemStack(ItemClass.GetItem(weapon,false),1);var parameters=new object[]{objective,source};
   typeof(ForestWeaponChoice).GetMethod("Prefix",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,parameters);
   Check(((ItemStack)parameters[1]).itemValue.ItemClass.GetItemName()=="delveBoneDagger","choice maps "+weapon);Check(source.itemValue.ItemClass.GetItemName()==weapon,"original craft event untouched "+weapon);
   // Standalone objective fixture: no local-player journal exists on a dedicated server.
   quest.CurrentPhase=2;
   typeof(ObjectiveCraft).GetMethod("Current_CraftItem",BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic).Invoke(objective,new object[]{source});
   Check(objective.CurrentValue==1 && objective.Complete,"native craft objective advances for "+weapon);
  }
  Check(!ForestOnboarding.Starter("resourceWood"),"materials cannot complete weapon objective");
  SdtdConsole.Instance.Output("[Onboarding] PASS "+checks+" loaded early-perk, quest-chain and weapon-choice isolation checks; natural player completion remains acceptance work.");
 }catch(Exception ex){SdtdConsole.Instance.Output("[Onboarding] FAIL "+ex);}}
}


