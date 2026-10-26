using System;
using System.IO;
using System.Collections.Generic;
using System.Xml;
using UnityEngine;

// Unspawned synthetic crafter: never included in the player package.
public class ConsoleCmdForestReady:ConsoleCmdAbstract
{
    public override string[] getCommands(){return new[]{"forestready"};}
    public override string getDescription(){return "Check every Forest recipe's native crafting gates and ingredients.";}
    static void Check(bool ok,string message){if(!ok)throw new Exception(message);}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        EntityPlayer player=null;
        try {
            player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),Vector3.zero) as EntityPlayer;
            player.world=GameManager.Instance.World;player.Progression.Level=1;
            foreach(string skill in new[]{"Farming","Cooking","Mining","Smithing","Carpentry","Alchemy"})
                Delve.CharacterProgression.Set(player,"delvePractice"+skill,Delve.ProficiencyRules.Threshold(20));
            var loaded=new Dictionary<string,Recipe>();
            foreach(var r in CraftingManager.GetAllRecipes()) {
                if(r.IsScrap)continue;
                string key=Delve.ForestSliceCatalog.Key(r);
                if(Delve.ForestSliceCatalog.Rank(r)<=20)loaded[key]=r;
            }
            var doc=new XmlDocument();doc.Load(Path.Combine((ModManager.GetMod("AlliumTools",false) ?? ModManager.GetMod("AccessProbe",true)).Path,"slice-checks.xml"));
            int count=0;
            foreach(XmlElement row in doc.SelectNodes("/slice/recipe")) {
                string key=row.GetAttribute("key"),name=row.GetAttribute("name"),skill=row.GetAttribute("skill");int rank=int.Parse(row.GetAttribute("rank"));
                Recipe r;Check(loaded.TryGetValue(key,out r),"Missing live variant: "+key);
                Check(Delve.ForestSliceCatalog.Rank(r)==rank,"Wrong rank: "+name);
                if(skill!="")Delve.CharacterProgression.Set(player,"delvePractice"+skill,Delve.ProficiencyRules.Threshold(rank));
                Check(r.IsUnlocked(player),"Native unlock at character 1 / proficiency "+rank+": "+name);
                Check(r.CanCraft(new List<ItemStack>(r.ingredients),player,-1),"Native ingredients/gate: "+key);
                Check(!r.CanCraft(new List<ItemStack>(),player,-1),"Missing ingredients accepted: "+name);
                if(rank>1 && skill!="") {
                    Delve.CharacterProgression.Set(player,"delvePractice"+skill,Delve.ProficiencyRules.Threshold(rank-1));
                    Check(!r.IsUnlocked(player) && !r.CanCraft(new List<ItemStack>(r.ingredients),player,-1),"Below-rank allowed: "+name);
                }
                if(skill!="")Delve.CharacterProgression.Set(player,"delvePractice"+skill,Delve.ProficiencyRules.Threshold(20));
                count++;
            }
            Check(count==loaded.Count,"Uncatalogued early recipe in engine");
            var aloe=CraftingManager.GetRecipe("plantedAloe1");
            Check(aloe!=null && !Delve.RecipeProgression.Allowed(aloe,player),"Desert aloe accidentally in Forest tier");
            // Even with all proficiency values high, an unaudited native station
            // variant cannot bypass the Forest recipe gate via a shared output.
            foreach(var r in CraftingManager.GetAllRecipes()) {
                if(!r.IsScrap && Delve.ForestSliceCatalog.Rank(r)>20)
                    Check(!Delve.RecipeProgression.Allowed(r,player),"Unsupported variant exposed: "+r.GetName());
            }
            SdtdConsole.Instance.Output("[ForestReady] PASS "+count+" exact recipe variants: native unlock/craft, missing ingredients, rank boundaries, character-level independence, and later-content exclusion.");
        }catch(Exception ex){SdtdConsole.Instance.Output("[ForestReady] FAIL "+ex);}
        finally {if(player!=null)UnityEngine.Object.Destroy(player.gameObject);}
    }
}

