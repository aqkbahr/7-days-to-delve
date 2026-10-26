using System;using System.Collections.Generic;using System.IO;using Delve;using UnityEngine;
public class ConsoleCmdRank20Probe:ConsoleCmdAbstract {
 static int count;static void Check(bool ok,string name){count++;if(!ok)throw new Exception(name);}
 public override string[] getCommands(){return new[]{"rank20verify"};}
 public override string getDescription(){return "Isolated maker-property and Arbor definition/consumption fixtures; not human gameplay acceptance.";}
 static ItemValue Item(string name){return new ItemValue(ItemClass.GetItem(name,false).type,1,1,false,null,1);}
 public override void Execute(List<string> args,CommandSenderInfo sender){EntityAlive player=null;try{
  count=0;
  var recipe=CraftingManager.GetRecipe("delveArborProtection");Check(recipe!=null,"Arbor recipe exists");Check(recipe.craftingArea=="delveMortarKit","Arbor station");
  player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),Vector3.zero) as EntityAlive;Check(player!=null,"player fixture");player.world=GameManager.Instance.World;
  CharacterProgression.Set(player,"delvePracticeAlchemy",ProficiencyRules.Threshold(19));Check(!RecipeProgression.Allowed(recipe,player),"Arbor locked below twenty");
  CharacterProgression.Set(player,"delvePracticeAlchemy",ProficiencyRules.Threshold(20));Check(RecipeProgression.Allowed(recipe,player),"Arbor unlocks at twenty");
  var protection=BuffManager.GetBuff("delveArborProtected");Check(protection!=null&&protection.DurationMax==600,"ten minute protection");
  player.Buffs.AddBuff("delveArborProtected");player.Buffs.Tick();Check(player.Buffs.HasBuff("delveArborProtected"),"protection applies");
  player.Buffs.AddBuff("delveArborProtected");player.Buffs.Tick();Check(player.Buffs.HasBuff("delveArborProtected"),"protection refresh applies");
  var storm=BuffManager.GetBuff("buffBurnt_Storm_Stage02");var context=new MinEventParams{Self=player,Other=player,IsLocal=true};
  int protectedHealth=player.Health;storm.Effects.FireEvent(MinEventTypes.onSelfBuffUpdate,context);Check(player.Health==protectedHealth,"protected native storm health effect suppressed");
  player.Buffs.RemoveBuff("delveArborProtected");player.Buffs.Tick();player.Health=player.GetMaxHealth();int unprotectedHealth=player.Health;storm.Effects.FireEvent(MinEventTypes.onSelfBuffUpdate,context);Check(player.Health==unprotectedHealth-2,"unprotected native storm damage resumes");
  player.Buffs.AddBuff("delveArborProtected");player.Buffs.Tick();var timed=player.Buffs.GetBuff("delveArborProtected");timed.DurationInTicks=11998;player.Buffs.Tick();Check(player.Buffs.HasBuff("delveArborProtected"),"protection before expiry");timed.DurationInTicks=12000;player.Buffs.Tick();player.Buffs.Tick();Check(!player.Buffs.HasBuff("delveArborProtected"),"native ten-minute expiration");
  Check(protection.RemoveOnDeath,"protection removed on death by native buff policy");
  foreach(string name in new[]{"foodDelveTrailRations","foodDelveTrailRation","foodDelveTravelBread","foodDelveBerryPreserve","foodDelveHoneyberryCakes"}){
   var food=Item(name);var ordinary=food.ItemClass.MaxCount;var r=CraftingManager.GetRecipe(name);Check(r!=null,"food recipe "+name);
   CraftedProperties.Stamp(food,r,128|Rank20Crafting.Hearty|Rank20Crafting.Trail|Rank20Crafting.Lasting);
   Check(food.ItemClass.GetItemName()==name+"DelvePacked","packed variant "+name);Check(food.ItemClass.MaxCount==ordinary*5/4,"packed stack capacity "+name);
   Check(Rank20Crafting.Marked(food,Rank20Crafting.Hearty)&&Rank20Crafting.Marked(food,Rank20Crafting.Lasting),"food traits "+name);
   var stream=new MemoryStream();var writer=new PooledBinaryWriter();writer.SetBaseStream(stream);food.Write(writer);writer.Flush();stream.Position=0;var reader=new PooledBinaryReader();reader.SetBaseStream(stream);var restored=new ItemValue();restored.Read(reader);
   Check(restored.type==food.type&&Rank20Crafting.Marked(restored,Rank20Crafting.Hearty),"food metadata roundtrip "+name);
  }
  var dagger=Item("delveIronDagger");float damage=EffectManager.GetValue(PassiveEffects.EntityDamage,dagger);CraftedProperties.Stamp(dagger,CraftingManager.GetRecipe("delveIronDagger"),128|Rank20Crafting.Honed);Check(Rank20Crafting.Marked(dagger,Rank20Crafting.Honed),"honed maker flag");Check(Math.Abs(EffectManager.GetValue(PassiveEffects.EntityDamage,dagger)-damage*1.05f)<.01f,"honed native damage");
  Check(!Rank20Crafting.Marked(Item("delveIronDagger"),Rank20Crafting.Honed),"unmarked loot unaffected");
  var ordinaryFood=Item("foodDelveTravelBread");player.Buffs.SetCustomVar("$foodAmountAdd",0);ordinaryFood.ItemClass.FireEvent(MinEventTypes.onSelfPrimaryActionEnd,new MinEventParams{Self=player,Other=player,ItemValue=ordinaryFood,IsLocal=true});float baseFood=player.Buffs.GetCustomVar("$foodAmountAdd");Check(baseFood>0,"native food nutrition event");
  var heartyFood=Item("foodDelveTravelBread");CraftedProperties.Stamp(heartyFood,CraftingManager.GetRecipe("foodDelveTravelBread"),128|Rank20Crafting.Hearty);player.Buffs.SetCustomVar("$foodAmountAdd",0);heartyFood.ItemClass.FireEvent(MinEventTypes.onSelfPrimaryActionEnd,new MinEventParams{Self=player,Other=player,ItemValue=heartyFood,IsLocal=true});Check(Math.Abs(player.Buffs.GetCustomVar("$foodAmountAdd")-baseFood*1.15f)<.01f,"crafted hearty nutrition gain");
  foreach(string name in new[]{"delveLesserHealingPotion","delveLesserStaminaPotion"}){
   var potion=Item(name);CraftedProperties.Stamp(potion,CraftingManager.GetRecipe(name),128|Rank20Crafting.Brews);Check(Rank20Crafting.Marked(potion,Rank20Crafting.Brews),"crafted potion trait "+name);
   player.Health=10;player.Stamina=10;float prior=name=="delveLesserHealingPotion"?player.Health:player.Stamina;
   potion.ItemClass.FireEvent(MinEventTypes.onSelfPrimaryActionEnd,new MinEventParams{Self=player,Other=player,ItemValue=potion,IsLocal=true});float raised=(name=="delveLesserHealingPotion"?player.Health:player.Stamina)-prior;Check(raised>0,"crafted potion native effect "+name);
   var plain=Item(name);player.Health=10;player.Stamina=10;prior=name=="delveLesserHealingPotion"?player.Health:player.Stamina;plain.ItemClass.FireEvent(MinEventTypes.onSelfPrimaryActionEnd,new MinEventParams{Self=player,Other=player,ItemValue=plain,IsLocal=true});float baseGain=(name=="delveLesserHealingPotion"?player.Health:player.Stamina)-prior;Check(Math.Abs(raised-baseGain*1.15f)<=1,"crafted potion fifteen-percent gain "+name+" actual="+raised+" base="+baseGain);
  }
  Check(Rank20Crafting.Extracts(CraftingManager.GetRecipe("delveHerbalExtract")),"herbal extraction eligible");
  Check(!Rank20Crafting.Extracts(CraftingManager.GetRecipe("delveLesserHealingPotion")),"final potion excluded from extraction yield");
  Check(!Rank20Crafting.Extracts(CraftingManager.GetRecipe("delveArborProtection")),"protection excluded from extraction yield");
  var station=new TileEntityWorkstation((Chunk)null);station.SetDisableModifiedCheck(true);var extract=CraftingManager.GetRecipe("delveHerbalExtract");
  var handle=typeof(TileEntityWorkstation).GetMethod("HandleRecipeQueue",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic);
  for(int i=0;i<20;i++){var job=new RecipeQueueItem{Recipe=extract,Multiplier=1,CraftingTimeLeft=0,OneItemCraftTime=1,Quality=1,StartingEntityId=player.entityId};CraftedProperties.Data.GetOrCreateValue(job).Flags=128|Rank20Crafting.Extraction;station.Queue=new[]{job};handle.Invoke(station,new object[]{2f});}
  int extracted=0;foreach(var stack in station.Output)if(stack.itemValue.type==extract.itemValueType)extracted+=stack.count;
  Check(extracted==extract.count*23,"native extraction yield across twenty separate jobs: "+extracted);Check(Math.Abs(Rank20StationCredits.Data.GetOrCreateValue(station).Extraction)<.0001f,"station extraction fractional remainder");
  var forge=new TileEntityWorkstation((Chunk)null);forge.SetDisableModifiedCheck(true);Recipe iron=null;foreach(var r in CraftingManager.GetAllRecipes())if(r.GetName()=="resourceForgedIron"&&r.craftingArea=="delveForgeAnvil"){iron=r;break;}Check(iron!=null,"owned forge recipe variant");int fuel=0;foreach(var ingredient in iron.ingredients)if(ingredient.itemValue.ItemClass.GetItemName()=="delveCharcoal")fuel=ingredient.count;Check(fuel>0,"owned forge recipe consumes charcoal");
  for(int i=0;i<20;i++){var job=new RecipeQueueItem{Recipe=iron,Multiplier=1,CraftingTimeLeft=0,OneItemCraftTime=1,Quality=1,StartingEntityId=player.entityId};CraftedProperties.Data.GetOrCreateValue(job).Flags=128|Rank20Crafting.Smelting;forge.Queue=new[]{job};handle.Invoke(forge,new object[]{2f});}
  int returnedFuel=0;foreach(var stack in forge.Output)if(stack!=null&&!stack.IsEmpty()&&stack.itemValue.ItemClass.GetItemName()=="delveCharcoal")returnedFuel+=stack.count;Check(returnedFuel==fuel*3,"native twenty-job charcoal savings: "+returnedFuel);
  var saved=Rank20StationCredits.Data.GetOrCreateValue(forge);saved.Fuel=.45f;saved.Extraction=.6f;
  foreach(var mode in new[]{StreamModeWrite.Persistency,StreamModeWrite.ToServer,StreamModeWrite.ToClient}){
   var data=new MemoryStream();var writer=new PooledBinaryWriter();writer.SetBaseStream(data);forge.write(writer,mode);writer.Write(1234567);writer.Flush();byte[] bytes=data.ToArray();
   int header=mode==StreamModeWrite.Persistency?22:12;Check(bytes[header]==Rank20StationCredits.Version,"station version marker "+mode);
   data.Position=0;var reader=new PooledBinaryReader();reader.SetBaseStream(data);var restoredStation=new TileEntityWorkstation(new Chunk(0,0));restoredStation.SetDisableModifiedCheck(true);restoredStation.read(reader,(StreamModeRead)(int)mode);
   var credit=Rank20StationCredits.Data.GetOrCreateValue(restoredStation);Check(Math.Abs(credit.Fuel-.45f)<.0001f&&Math.Abs(credit.Extraction-.6f)<.0001f,"station credits survive "+mode);Check(reader.ReadInt32()==1234567,"station extension boundary "+mode);
   var legacy=new byte[bytes.Length-8];Array.Copy(bytes,legacy,bytes.Length-12);Array.Copy(bytes,bytes.Length-4,legacy,legacy.Length-4,4);legacy[header]=50;
   reader=new PooledBinaryReader();reader.SetBaseStream(new MemoryStream(legacy));restoredStation=new TileEntityWorkstation(new Chunk(0,0));restoredStation.SetDisableModifiedCheck(true);restoredStation.read(reader,(StreamModeRead)(int)mode);credit=Rank20StationCredits.Data.GetOrCreateValue(restoredStation);
   Check(credit.Fuel==0&&credit.Extraction==0&&reader.ReadInt32()==1234567,"native station compatibility "+mode);
  }
  player.Progression.GetProgressionValue("delvePerkCarpentryEfficientFraming").Level=1;
  var crate=CraftingManager.GetRecipe("cntWoodWritableCrate");Check(EffectManager.GetValue(PassiveEffects.CraftingIngredientCount,null,10,player,crate,FastTags<TagGroup.Global>.Parse("resourceWood"))==9,"construction ingredient discount");
  Check(EffectManager.GetValue(PassiveEffects.CraftingIngredientCount,null,10,player,crate,FastTags<TagGroup.Global>.Parse("resourceNail"))==10,"nonwood ingredient unaffected");
  SdtdConsole.Instance.Output("[Rank20] PASS "+count+" native definition, gating, maker effect, item serialization and buff-application checks. Hazard damage, expiry, combat and multiplayer acceptance remain separate.");
 }catch(Exception ex){SdtdConsole.Instance.Output("[Rank20] FAIL "+ex);}finally{if(player!=null)UnityEngine.Object.Destroy(player.gameObject);}}
}
