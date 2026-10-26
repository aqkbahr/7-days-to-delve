using System;using System.IO;using System.Xml;using System.Collections.Generic;using System.Reflection;using Delve;using UnityEngine;
public class StationToolFixture:XUiC_WorkstationToolGrid {
 public ItemStack[] Slots;public override ItemStack[] getUISlots(){return Slots;}
}
public class ConsoleCmdStationProbe:ConsoleCmdAbstract {
 static int count;static void Check(bool b,string message){count++;if(!b)throw new Exception(message);}
 public override string[] getCommands(){return new[]{"stationverify"};}
 public override string getDescription(){return "Native station recipe, add-on, proficiency and serialization fixtures.";}
 static ItemStack Stack(string name){return new ItemStack(ItemClass.GetItem(name,false),1);}
 public override void Execute(List<string> args,CommandSenderInfo sender){EntityAlive player=null;bool oldWorkstation=XUiM_Recipes.WorkstationCrafting;var oldBackpack=XUiM_Recipes.BackpackCrafting;try{
  XUiM_Recipes.WorkstationCrafting=true;XUiM_Recipes.BackpackCrafting=(BackpackCraftingOptions)1;
  count=0;var doc=new XmlDocument();doc.Load(args[0]);var core=Core.VerifyDefinitions();Check(core.StartsWith("PASS:"),core);SdtdConsole.Instance.Output(core);
  var recipes=new Dictionary<string,Recipe>();foreach(var r in CraftingManager.GetAllRecipes()){string k=ForestSliceCatalog.Key(r);if(!recipes.ContainsKey(k))recipes.Add(k,r);}
  player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),Vector3.zero) as EntityAlive;Check(player!=null,"player fixture");player.world=GameManager.Instance.World;
  var grid=new StationToolFixture();int tested=0;
  foreach(XmlElement e in doc.SelectNodes("/checks/recipe")){
   string key=e.GetAttribute("key"),skill=e.GetAttribute("skill"),tool=e.GetAttribute("tool");int rank=int.Parse(e.GetAttribute("rank"));Recipe r;
   Check(recipes.TryGetValue(key,out r),"missing recipe "+key);Check(ForestSliceCatalog.Rank(r)==rank,"rank "+key);
   Check((TrainingHooks.CraftedSkill(r.GetName(),r.craftingArea)??"")==skill,"practice owner "+key+" actual="+TrainingHooks.CraftedSkill(r.GetName(),r.craftingArea));
   if(skill!="")CharacterProgression.Set(player,"delvePractice"+skill,ProficiencyRules.Threshold(rank));Check(RecipeProgression.Allowed(r,player),"unlock "+key);
   Check(r.IsUnlocked((EntityPlayer)player)&&r.CanCraft(new List<ItemStack>(r.ingredients),player,-1),"native unlock and ingredients "+key);
   if(rank>1&&skill!=""){CharacterProgression.Set(player,"delvePractice"+skill,ProficiencyRules.Threshold(rank-1));Check(!RecipeProgression.Allowed(r,player),"premature unlock "+key);}
   Check(r.craftingToolType==(tool==""?0:ItemClass.GetItem(tool,false).type),"tool mapping "+key);
   grid.Slots=new[]{ItemStack.Empty.Clone()};Check(grid.HasRequirement(r)==(tool==""),"empty tool slot "+key);
   if(tool!=""){
    grid.Slots=new[]{Stack("resourceWood")};Check(!grid.HasRequirement(r),"wrong tool "+key);
    grid.Slots=new[]{Stack(tool)};Check(grid.HasRequirement(r),"installed tool "+key);
    grid.Slots=new[]{ItemStack.Empty.Clone()};Check(!grid.HasRequirement(r),"removed tool "+key);
   }
   tested++;
  }
  SdtdConsole.Instance.Output("[StationProbe] Recipes passed: "+tested);
  foreach(XmlElement e in doc.SelectNodes("/checks/station")){
   string name=e.GetAttribute("name");var block=Block.GetBlockValue(name,false).Block;Check(block is BlockWorkstation,"workstation "+name);
   var ws=((BlockWorkstation)block).WorkstationData;Check(ws!=null,"registered workstation "+name);Check(ws.WorkstationWindow=="workstation_"+e.GetAttribute("base"),"window "+name);
   var menu=XUiM_Recipes.FilterRecipesByWorkstation(e.GetAttribute("base"),CraftingManager.GetAllRecipes());var aliases=new HashSet<string>(e.GetAttribute("aliases").Split(','));
   foreach(XmlElement row in doc.SelectNodes("/checks/recipe")){var r=recipes[row.GetAttribute("key")];Check(menu.Contains(r)==aliases.Contains(r.craftingArea??""),"native menu "+name+" / "+r.GetName());}
   var names=e.GetAttribute("tools").Split(',');var station=new TileEntityWorkstation((Chunk)null);station.SetDisableModifiedCheck(true);
   var slots=new ItemStack[names.Length];for(int i=0;i<slots.Length;i++)slots[i]=Stack(names[i]);station.Tools=slots;
   foreach(var mode in new[]{StreamModeWrite.Persistency,StreamModeWrite.ToServer,StreamModeWrite.ToClient}){
    var ms=new MemoryStream();var writer=new PooledBinaryWriter();writer.SetBaseStream(ms);station.write(writer,mode);writer.Write(1234567);writer.Flush();ms.Position=0;
    var reader=new PooledBinaryReader();reader.SetBaseStream(ms);var loaded=new TileEntityWorkstation(new Chunk(0,0));loaded.SetDisableModifiedCheck(true);loaded.read(reader,(StreamModeRead)(int)mode);
    Check(reader.ReadInt32()==1234567,"serialization boundary "+name+" "+mode);Check(loaded.Tools.Length==slots.Length,"tool count "+name+" "+mode);
    for(int i=0;i<slots.Length;i++)Check(loaded.Tools[i].itemValue.type==slots[i].itemValue.type&&loaded.Tools[i].count==1,"saved tool "+name+" "+mode+" "+i);
   }
  }
  foreach(XmlElement e in doc.SelectNodes("/checks/retired"))Check(CraftingManager.GetRecipe(e.GetAttribute("name"))==null,"retired station craftable");
  int queued=0;var handle=typeof(TileEntityWorkstation).GetMethod("HandleRecipeQueue",BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic);
  foreach(XmlElement e in doc.SelectNodes("/checks/recipe[@queue='true']")){
   var r=recipes[e.GetAttribute("key")];var station=new TileEntityWorkstation((Chunk)null);station.SetDisableModifiedCheck(true);
   station.Tools=new[]{Stack(e.GetAttribute("tool"))};station.Queue=new[]{new RecipeQueueItem{Recipe=r,Multiplier=1,CraftingTimeLeft=0,OneItemCraftTime=1,Quality=1,StartingEntityId=-1}};
   handle.Invoke(station,new object[]{2f});int output=0;foreach(var s in station.Output)if(s!=null&&s.itemValue.type==r.itemValueType)output+=s.count;Check(output==r.count,"queue output "+e.GetAttribute("key"));queued++;
  }
  SdtdConsole.Instance.Output("[StationProbe] PASS "+count+" checks; "+tested+" recipe variants; "+queued+" native queues; native missing/wrong/installed/removed tool requirements; "+doc.SelectNodes("/checks/station").Count+" station variants with 2/3 tool slots across persistence and both network modes.");
 }catch(Exception ex){SdtdConsole.Instance.Output("[StationProbe] FAIL "+ex);}finally{XUiM_Recipes.WorkstationCrafting=oldWorkstation;XUiM_Recipes.BackpackCrafting=oldBackpack;if(player!=null)UnityEngine.Object.Destroy(player.gameObject);}}
}
