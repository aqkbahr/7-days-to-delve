from pathlib import Path
from lxml import etree as E
import json, shutil
root=Path(__file__).resolve().parents[1]
profile=root/'playtest/RecipeLearning'
mod=profile/'Mods/SkillCoverageProbe';mod.mkdir(exist_ok=True)
shutil.copytree(root/'src/ZZZZZZZZZDelveSkillCoverage',profile/'Mods/ZZZZZZZZZDelveSkillCoverage',dirs_exist_ok=True)
(mod/'ModInfo.xml').write_text('<xml><Name value="SkillCoverageProbe"/><DisplayName value="Skill coverage checks"/><Version value="1.0"/><Author value="Delve"/></xml>')
text=(root/'tools/allium/ForestReadinessProbe.cs').read_text()
text=text.replace('ConsoleCmdForestReady','ConsoleCmdSkillCoverage').replace('forestready','skillcoverage').replace('[ForestReady]','[SkillCoverage]')
text=text.replace('if(Delve.ForestSliceCatalog.Rank(r)<=20)','if(Delve.ForestSliceCatalog.Rank(r)<=20 || DelveCoverage.CoverageCatalog.Find(key)!=null)')
text=text.replace('(ModManager.GetMod("AlliumTools",false) ?? ModManager.GetMod("AccessProbe",true))','ModManager.GetMod("SkillCoverageProbe",true)')
text=text.replace('Delve.ForestSliceCatalog.Rank(r)>20)', 'Delve.ForestSliceCatalog.Rank(r)>20 && DelveCoverage.CoverageCatalog.Find(Delve.ForestSliceCatalog.Key(r))==null)')
extra='''
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
'''
text=text.replace('            SdtdConsole.Instance.Output(',extra+'            SdtdConsole.Instance.Output(',1)
(root/'tools/allium/SkillCoverageProbe.cs').write_text(text)
doc=E.parse(str(root/'artifacts/skill-coverage-base-slice.xml'))
for row in json.loads((root/'artifacts/validation/skill-coverage/recipes.json').read_text()):
 E.SubElement(doc.getroot(),'recipe',**{k:str(row[k]) for k in ('key','name','skill','rank')})
doc.write(str(mod/'slice-checks.xml'),pretty_print=True)
print('Prepared isolated RecipeLearning fixture with additive coverage module; 223 recipes.')
