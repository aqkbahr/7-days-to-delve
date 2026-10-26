namespace Delve {
 public static class SummoningUi {
  public static SkillUiDefinition Skill(){var p=new PerkUiDefinition[14];
   p[0]=new PerkUiDefinition("delvePerkSummoningBindingDiscipline","Binding Discipline","+10% summoning rod reload speed. Native ammunition consumption is unchanged.");
   p[1]=new PerkUiDefinition("delvePerkSummoningPrimalBond","Primal Bond","New summons have 15% more maximum health. Applied when summoned; stacks multiplicatively with rod quality and the Forged rod bonus.");
   p[2]=new PerkUiDefinition("delvePerkSummoningFierceCompanion","Fierce Companion","New summons deal 20% more damage. Applied when summoned; damage still respects enemy mitigation.");
   p[6]=new PerkUiDefinition("delvePerkSummoningStalwartCompanion","Stalwart Companion","New summons take 15% less incoming damage from hostile creatures. Friendly-fire protection remains unchanged.");
   p[10]=new PerkUiDefinition("delvePerkSummoningEnduringPact","Enduring Pact","New summons last 75 seconds instead of 60. Still one summon per caster; recasting replaces it. Death and disconnect cleanup are unchanged.");
   return new SkillUiDefinition("Summoning","Summoning",1,"Train through companion damage. Two fundamentals at 10; three branches at 20. Forged rods: Carpentry 20.",new[]{"Ferocity","Guardianship","Binding"},p);
  }
 }
}
