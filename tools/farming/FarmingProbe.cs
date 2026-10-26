using System;
using System.IO;
using System.Xml;
using System.Collections.Generic;
using UnityEngine;

public class ConsoleCmdFarmingVerify : ConsoleCmdAbstract
{
    static int checks;
    static void Check(bool ok,string why){if(!ok)throw new Exception(why);checks++;}
    public override string[] getCommands(){return new[]{"farmingverify"};}
    public override string getDescription(){return "Verify first-pass farming in the isolated test profile.";}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        EntityAlive fixture=null;
        try {
            checks=0;
            var doc=new XmlDocument();doc.Load(Path.Combine(ModManager.GetMod("FarmingProbe",true).Path,"farming-checks.xml"));
            fixture=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),Vector3.zero) as EntityAlive;
            Check(fixture!=null,"player fixture");fixture.world=GameManager.Instance.World;
            fixture.Progression.Level=1;
            foreach(XmlElement row in doc.SelectNodes("/farming/recipes/entry")) {
                string name=row.GetAttribute("name"),skill=row.GetAttribute("skill");int rank=int.Parse(row.GetAttribute("rank"));
                var recipe=CraftingManager.GetRecipe(name);Check(recipe!=null,"recipe "+name);
                Check(recipe.count==int.Parse(row.GetAttribute("count")),"batch "+name);
                Check((recipe.craftingArea ?? "")==row.GetAttribute("station"),"station recipe "+name);
                Check((Delve.TrainingHooks.CraftedSkill(name,recipe.craftingArea) ?? "")==row.GetAttribute("skill"),"practice owner "+name);
                if(rank>20){Check(!Delve.RecipeProgression.Allowed(recipe,fixture),"later biome excluded "+name);continue;}
                if(skill!="")Delve.CharacterProgression.Set(fixture,"delvePractice"+skill,Delve.ProficiencyRules.Threshold(rank));
                Check(Delve.RecipeProgression.Allowed(recipe,fixture),"unlock at proficiency "+name);
                if(rank>1 && skill!=""){
                    Delve.CharacterProgression.Set(fixture,"delvePractice"+skill,Delve.ProficiencyRules.Threshold(rank-1));
                    Check(!Delve.RecipeProgression.Allowed(recipe,fixture),"lock below proficiency "+name);
                }
            }
            foreach(XmlElement row in doc.SelectNodes("/farming/stations/entry")) {
                string name=row.GetAttribute("name");var block=Block.GetBlockValue(name,false).Block;
                Check(block is BlockWorkstation,"workstation class "+name);
                var data=CraftingManager.GetWorkstationData(name);
                Check(data!=null && data.WorkstationWindow=="workstation_"+name,"UI registration "+name);
                Check(block.itemsToDrop[EnumDropEvent.Destroy][0].minCount==0,"no salvage duplication "+name);
            }
            foreach(XmlElement row in doc.SelectNodes("/farming/seeds/entry")) {
                var block=Block.GetBlockValue(row.GetAttribute("ripe"),false).Block;
                bool guaranteed=false;
                foreach(var drop in block.itemsToDrop[EnumDropEvent.Destroy])
                    if(drop.name==row.GetAttribute("seed") && drop.prob==1 && drop.minCount==1)guaranteed=true;
                Check(guaranteed,"guaranteed replanting "+row.GetAttribute("seed"));
            }
            foreach(XmlElement row in doc.SelectNodes("/farming/orders/entry")) {
                var q=QuestClass.CreateQuest(row.GetAttribute("quest"));
                Check(q!=null && q.QuestClass.Repeatable && !q.QuestClass.Shareable,"repeatable private order");
                Check(q.Objectives.Count==1 && q.Objectives[0] is ObjectiveFetch,"single delivery objective");
                var objective=(ObjectiveFetch)q.Objectives[0];
                Check(!objective.KeepItems && objective.ID==row.GetAttribute("parcel"),"consuming delivery");
            }
            var meal=ItemClass.GetItem("foodDelveTrailRation",false);
            meal.ItemClass.FireEvent(MinEventTypes.onSelfPrimaryActionEnd,new MinEventParams{Self=fixture,ItemValue=meal});
            Check(fixture.Buffs.GetCustomVar("$foodAmountAdd")==55,"ration nutrition");
            var medicine=ItemClass.GetItem("medicalDelveYarrowTincture",false);
            medicine.ItemClass.FireEvent(MinEventTypes.onSelfPrimaryActionEnd,new MinEventParams{Self=fixture,ItemValue=medicine});
            Check(fixture.Buffs.GetCustomVar("medicalRegHealthAmount")==35,"tincture recovery");
            SdtdConsole.Instance.Output("[Farming] PASS "+checks+" engine checks: recipes, proficiency gates at character level 1, practice ownership, stations, seeds, consuming objectives and consumables.");
        }catch(Exception ex){SdtdConsole.Instance.Output("[Farming] FAIL "+ex);}
        finally{if(fixture!=null)UnityEngine.Object.Destroy(fixture.gameObject);}
    }
}
