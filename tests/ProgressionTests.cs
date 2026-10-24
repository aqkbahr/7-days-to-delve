using System;
using System.Collections.Generic;
using Delve;
public class ProgressionTests
{
 static int count;
 static void Check(bool ok,string name){if(!ok)throw new Exception(name);count++;Console.WriteLine("PASS "+name);}
 public static void Main()
 {
  var owned=new HashSet<string>();
  var branch=new TalentDefinition("Blades",20,true,new[]{"a","b"});
  Check(!branch.CanBuy(20,false,false,owned.Contains),"both fundamentals required");
  owned.Add("a"); Check(!branch.CanBuy(20,false,false,owned.Contains),"one fundamental insufficient");
  owned.Add("b");Check(branch.CanBuy(20,false,false,owned.Contains),"branch unlock with both fundamentals");
  Check(!branch.CanBuy(19,false,false,owned.Contains),"proficiency gate enforced");
  var cap=new TalentDefinition("Blades",100,true,new[]{"a","b"});
  Check(!cap.CanBuy(100,false,false,owned.Contains),"mastery requires trial");
  Check(!cap.CanBuy(100,true,true,owned.Contains),"second capstone rejected");
  Check(cap.CanBuy(100,true,false,owned.Contains),"one eligible capstone accepted");
  Check(!new TalentDefinition("Blades",10,false,new string[0]).CanBuy(100,true,false,owned.Contains),"unimplemented effects cannot cost points");
  Check(ProgressionMath.PackedLoad(new[]{100},new[]{100},10)==.1f,"one full stack counts one slot");
  Check(ProgressionMath.PackedLoad(new[]{50,50},new[]{100,100},10)==.1f,"stack splitting cannot inflate load");
  Check(ProgressionMath.PackedLoad(new[]{1,1},new[]{1,1},4)==.5f,"nonstackable equipment counts full slots");
  Check(ProgressionMath.PackedLoad(new[]{1},new[]{0},4)==0,"invalid stack sizes excluded");
  Check(ProgressionMath.PackedLoad(new[]{999},new[]{1},4)==1,"fullness caps at one");
  Check(Math.Abs(ProgressionMath.RecipeDuration(153,.38f,.15f)-100)<.001,"craft speeds add before dividing duration");
  foreach(string skill in ProficiencyRules.Skills)
  {
   int ordinary=0,masteries=0;
   foreach(var pair in TalentCatalog.Entries) if(pair.Value.Skill==skill)
   {
    var d=pair.Value;
    if(d.Rank==100){masteries++;Check(d.Prerequisites.Length==14,skill+" capstone requires all 14");}
    else {ordinary++;Check(d.Prerequisites.Length==(d.Rank==10?0:d.Rank==20?2:1),skill+" branch dependency count");}
    foreach(string prior in d.Prerequisites)Check(TalentCatalog.Entries.ContainsKey(prior)&&TalentCatalog.Entries[prior].Skill==skill&&TalentCatalog.Entries[prior].Rank<d.Rank,skill+" valid earlier prerequisite");
   }
   Check(ordinary==14&&masteries>=4,skill+" complete 14+one structure");
  }
  Console.WriteLine(count+" progression checks passed.");
 }
}
