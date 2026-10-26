using System.Collections.Generic;
namespace Delve {
 public static class SummonTalents {
  public static readonly string[] Names={"BindingDiscipline","PrimalBond","FierceCompanion","StalwartCompanion","EnduringPact"};
  public static void Register(Dictionary<string,TalentDefinition> entries){for(int i=0;i<Names.Length;i++)entries["delvePerkSummoning"+Names[i]]=new TalentDefinition("Summoning",i<2?10:20,true,i<2?new string[0]:new[]{"delvePerkSummoningBindingDiscipline","delvePerkSummoningPrimalBond"});}
 }
}
