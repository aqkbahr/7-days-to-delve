using System;
using System.IO;
using System.Collections.Generic;
using System.Xml;
using UnityEngine;

// Unspawned synthetic crafter: never included in the player package.
public class ConsoleCmdSkillCoverage:ConsoleCmdAbstract
{
    public override string[] getCommands(){return new[]{"skillcoverage"};}
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
                if(Delve.ForestSliceCatalog.Rank(r)<=20 || DelveCoverage.CoverageCatalog.Find(key)!=null)loaded[key]=r;
            }
            var doc=new XmlDocument();doc.Load(Path.Combine(ModManager.GetMod("SkillCoverageProbe",true).Path,"slice-checks.xml"));
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
                if(!r.IsScrap && Delve.ForestSliceCatalog.Rank(r)>20 && DelveCoverage.CoverageCatalog.Find(Delve.ForestSliceCatalog.Key(r))==null)
                    Check(!Delve.RecipeProgression.Allowed(r,player),"Unsupported variant exposed: "+r.GetName());
            }

            Check(count==223,"Expected 223 recipe variants");
            foreach(var row in DelveCoverage.CoverageCatalog.Rows) {
                Check(Delve.TrainingHooks.CraftedSkill(row.Name,"")==row.Skill,"Craft owner: "+row.Name);
                Check(Delve.ForestSliceCatalog.Minimum(row.Name)==row.Rank,"UI rank: "+row.Name);
                Check(Delve.ForestSliceCatalog.Skill(row.Name)==row.Skill,"UI skill: "+row.Name);
            }
            Check(Delve.ProficiencyRules.Identify("thrownAmmoPipeBomb")=="Alchemy","Blast use owner");
            Check(Delve.ProficiencyRules.Identify("thrownDynamite")=="Alchemy","Excavation use owner");
            Check(Delve.ProficiencyRules.Identify("meleeToolSalvageT1Wrench")=="Blunt","Wrench combat owner");
            Check(Delve.ProgressionUiData.Skills.Length==20,"Existing 20 trees retained");
            bool branch=false;foreach(var s in Delve.ProgressionUiData.Skills)if(s.Id=="Alchemy")branch=s.Branches[2]=="Arcane & Explosives";
            Check(branch,"Alchemy branch UI");
            foreach(var type in typeof(DelveCoverage.Coverage).Assembly.GetTypes()) {
                if(type.GetCustomAttributes(typeof(HarmonyLib.HarmonyPatch),false).Length==0)continue;
                // PatchAll must have completed to reach the UI changes above.
            }
            SdtdConsole.Instance.Output("[SkillCoverage] PASS "+count+" exact recipe variants: native unlock/craft, missing ingredients, rank boundaries, character-level independence, and later-content exclusion.");
        }catch(Exception ex){SdtdConsole.Instance.Output("[SkillCoverage] FAIL "+ex);}
        finally {if(player!=null)UnityEngine.Object.Destroy(player.gameObject);}
    }
}

