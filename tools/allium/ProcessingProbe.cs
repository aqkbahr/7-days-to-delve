using System;
using System.Collections.Generic;
using System.Reflection;
using System.Xml;
using System.IO;
using UnityEngine;
public class ConsoleCmdProcessingVerify:ConsoleCmdAbstract
{
    static int checks;
    static void Check(bool value,string reason){if(!value)throw new Exception(reason);checks++;}
    public override string[] getCommands(){return new[]{"processingverify"};}
    public override string getDescription(){return "Validate M2 recipes, production, collector, repairs and food slots.";}
    static object Call(object target,string method,params object[] args){return target.GetType().GetMethod(method,BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic).Invoke(target,args);}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        EntityAlive player=null;
        try {
            if(!Delve.Core.VerifyDefinitions().StartsWith("PASS:")){SdtdConsole.Instance.Output("[Processing] Wait for the world to finish loading.");return;}
            checks=0;var doc=new XmlDocument();doc.Load(Path.Combine(ModManager.GetMod("AlliumTools",true).Path,"processing-checks.xml"));
            player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),Vector3.zero) as EntityAlive;player.world=GameManager.Instance.World;player.Progression.Level=20;
            foreach(XmlElement row in doc.SelectNodes("/processing/recipe")) {
                Recipe found=null;
                foreach(var r in CraftingManager.GetAllRecipes()) {
                    if(r.GetName()!=row.GetAttribute("name") || (r.craftingArea??"")!=row.GetAttribute("station") || r.count!=int.Parse(row.GetAttribute("count")))continue;
                    bool matches=r.ingredients.Count==row.SelectNodes("ingredient").Count;
                    foreach(XmlElement input in row.SelectNodes("ingredient")) {
                        bool present=false;foreach(var ingredient in r.ingredients)if(ingredient.itemValue.ItemClass.GetItemName()==input.GetAttribute("name") && ingredient.count==int.Parse(input.GetAttribute("count")))present=true;
                        matches&=present;
                    }
                    if(matches){found=r;break;}
                }
                Check(found!=null,"loaded recipe "+row.GetAttribute("name"));
                Check((Delve.TrainingHooks.CraftedSkill(found.GetName(),found.craftingArea)??"")==row.GetAttribute("skill"),"skill "+found.GetName());
                string skill=row.GetAttribute("skill");int rank=int.Parse(row.GetAttribute("rank"));
                if(skill!="") {
                    Delve.CharacterProgression.Set(player,"delvePractice"+skill,0);
                    if(rank>1)Check(!Delve.RecipeProgression.Allowed(found,player),"rank gate "+found.GetName());
                    Delve.CharacterProgression.Set(player,"delvePractice"+skill,1000000);
                    Check(Delve.RecipeProgression.Allowed(found,player),"eligible "+found.GetName());
                }
                if(!String.IsNullOrEmpty(found.craftingArea) && found.craftingArea.StartsWith("delve")) {
                    var te=new TileEntityWorkstation((Chunk)null);
                    te.SetDisableModifiedCheck(true); // Detached fixture: do not broadcast a nonexistent world tile.
                    te.Queue=new[]{new RecipeQueueItem{Recipe=found,Multiplier=1,CraftingTimeLeft=0,OneItemCraftTime=1,Quality=1,StartingEntityId=-1}};
                    Call(te,"HandleRecipeQueue",2f);
                    int output=0;foreach(var s in te.Output)if(s.itemValue.type==found.itemValueType)output+=s.count;
                    Check(output==found.count,"native queue output "+found.GetName());
                }
            }
            foreach(XmlElement s in doc.SelectNodes("/processing/station")) {
                string name=s.GetAttribute("name");Check(Block.GetBlockValue(name,false).Block is BlockWorkstation,"station "+name);
                Check(CraftingManager.GetWorkstationData(name).WorkstationWindow=="workstation_"+name,"station UI "+name);
            }
            foreach(XmlElement r in doc.SelectNodes("/processing/repair")) {
                var item=ItemClass.GetItem(r.GetAttribute("name"),false).ItemClass;
                Check(item.Properties.GetString("RepairTools")==r.GetAttribute("supply"),"repair binding "+r.GetAttribute("name"));
                Check(ItemClass.GetItem(r.GetAttribute("supply"),false).ItemClass.Properties.GetInt("RepairAmount")==32000,"repair capacity");
            }
            var collector=Block.GetBlockValue("delveRainCollector",false).Block as BlockCollector;
            Check(collector!=null,"native collector");var outputType=collector.GetOutputType("water");
            Check(outputType.MinConvertTime==500 && outputType.MaxConvertTime==1000,"collection interval");
            var chunk=new Chunk(0,0);chunk.SetBlockRaw(0,64,0,Block.GetBlockValue("delveRainCollector",false));
            var water=new TileEntityCollector(chunk);water.localChunkPos=new Vector3i(0,64,0);
            water.SetDisableModifiedCheck(true);
            typeof(TileEntityCollector).GetField("fuelSlotsInternal",BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public).SetValue(water,new[]{new ItemStack(ItemClass.GetItem("drinkJarEmpty",false),1)});
            var produced=(ItemStack)Call(water,"newItem",outputType,collector.GetFuelType("jar"));
            Check(produced!=null && produced.count==1 && produced.itemValue.ItemClass.GetItemName()=="drinkJarRiverWater","native water production");
            Check(water.FuelSlots[0].count==0,"container consumed");
            Check(Call(water,"newItem",outputType,collector.GetFuelType("jar"))==null,"cannot produce without container");
            float before=EffectManager.GetValue(PassiveEffects.StaminaMax,null,0,player);
            foreach(string name in new[]{"foodDelveGathererPorridge","foodDelveTrailRations","foodDelveGathererPorridge","drinkDelveGoldenrodTea"}) {
                var item=ItemClass.GetItem(name,false);item.ItemClass.FireEvent(MinEventTypes.onSelfPrimaryActionEnd,new MinEventParams{Self=player,ItemValue=item});
            }
            Check(player.Buffs.HasBuff("delveForestMeal") && player.Buffs.HasBuff("delveForestDrink"),"meal and drink coexist");
            Check(Math.Abs(EffectManager.GetValue(PassiveEffects.StaminaMax,null,0,player)-before-10)<.01,"repeated meals do not stack");
            SdtdConsole.Instance.Output("[Processing] PASS "+checks+" engine checks including native queue output, jar consumption, skill gates, repairs and meal/drink slots. Synthetic fixtures; client interactions require playtest.");
        }catch(Exception ex){SdtdConsole.Instance.Output("[Processing] FAIL "+ex);}
        finally{if(player!=null)UnityEngine.Object.Destroy(player.gameObject);}
    }
}
