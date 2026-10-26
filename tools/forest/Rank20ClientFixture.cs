using System;using System.Collections;using UnityEngine;using Delve;
public partial class EquipmentFixture {
 int Hit(EntityAlive target,string item,bool heavy,int amount){var previous=FirstTierCombat.Current;try{var source=new DamageSourceEntity(EnumDamageSource.External,EnumDamageTypes.Slashing,p.entityId){AttackingItem=ItemClass.GetItem(item,false)};source.SetIgnoreConsecutiveDamages(true);FirstTierCombat.Current=new FirstTierCombat.Swing{Player=p,Heavy=heavy,Skill=Rank20.Skill(source.AttackingItem)};int health=target.Health;target.DamageEntity(source,amount,false,0);report.AppendLine("HIT "+item+" heavy="+heavy+" amount="+amount+" dealt="+(health-target.Health));return health-target.Health;}finally{FirstTierCombat.Current=previous;}}
 IEnumerator CombatChecks(){
  EntityAlive target=null;float until=Time.realtimeSinceStartup+30;while(target==null&&Time.realtimeSinceStartup<until){foreach(var e in p.world.EntityAlives)if(EntityClass.GetEntityClassName(e.entityClass)=="delveCorruptedWalker"&&!e.IsDead()){target=e;break;}if(target==null)yield return null;}
  Check(target!=null,"actual server-spawned replicated combat target");int start=target.Health;
  foreach(string perk in new[]{"BladesPowerfulCuts","BladesExploitOpening","StealthOpeningStrike","PackMuleHeavyMomentum","WandsMeasuredBolt","StaffsOverload","StaffsFocusedImpact","BluntBrace","UnarmedFleetFoot","BladesDrawingBlood","BluntCrushingImpact","UnarmedCombination"})Perk(perk,false);
  try{
   Check(Hit(target,"delveBoneDagger",true,10)==10,"native baseline heavy damage10");yield return new WaitForSeconds(1.6f);Perk("BladesPowerfulCuts",true);Check(Hit(target,"delveBoneDagger",true,10)==12,"Powerful Cuts native heavy damage12");yield return new WaitForSeconds(1.6f);Check(Hit(target,"delveBoneDagger",false,10)==10,"Powerful Cuts excludes light damage");yield return new WaitForSeconds(1.6f);Perk("BladesPowerfulCuts",false);
   Perk("WandsMeasuredBolt",true);Check(Hit(target,"delveStarterWand",false,10)==11,"Measured Bolt native damage11");yield return new WaitForSeconds(1.6f);Perk("WandsMeasuredBolt",false);
   Perk("StaffsOverload",true);Check(Hit(target,"delveStarterStaff",false,20)==23,"Overload native primary damage23");yield return new WaitForSeconds(1.6f);Perk("StaffsOverload",false);
   Perk("StaffsFocusedImpact",true);Check(Hit(target,"delveStarterStaff",false,20)==23,"Focused Impact native primary damage23");yield return new WaitForSeconds(1.6f);Perk("StaffsFocusedImpact",false);
   var state=Rank20.States.GetOrCreateValue(p);state.BraceNext=0;Perk("BluntBrace",true);Check(Hit(target,"delveOakCudgel",true,1)>0&&state.BraceUntil>Time.time&&state.BraceNext>state.BraceUntil,"Brace arms from actual heavy damage with cooldown");yield return new WaitForSeconds(1.6f);Perk("BluntBrace",false);
   state.FleetNext=0;Perk("UnarmedFleetFoot",true);Check(Hit(target,"delveLeatherKnuckles",false,1)>0&&state.FleetUntil>Time.time&&state.FleetNext>state.FleetUntil,"Fleet Foot arms from actual hit with cooldown");Perk("UnarmedFleetFoot",false);
   report.AppendLine("NETWORK target="+target.entityId+" health="+start+" -> "+target.Health+" before fixture cleanup");
  }finally{if(target!=null&&!target.IsDead()){var source=new DamageSource(EnumDamageSource.External,EnumDamageTypes.Bashing);target.DamageEntity(source,10000,false,0);}var state=Rank20.States.GetOrCreateValue(p);state.BraceUntil=state.BraceNext=state.FleetUntil=state.FleetNext=0;}
  report.AppendLine("SCOPE actual connected-client DamageEntity path and server-spawned target; not input/raycast collision acceptance.");
 }
 float Value(PassiveEffects effect,string item="",string tags="",float basis=0){if(effect==PassiveEffects.ReloadSpeedMultiplier||effect==PassiveEffects.WalkSpeed)basis=1;var value=item==""?null:ItemClass.GetItem(item,false);var query=FastTags<TagGroup.Global>.Parse(tags);if(effect==PassiveEffects.AttacksPerMinute){basis=60;if(value!=null)query|=value.ItemClass.ItemTags;}return EffectManager.GetValue(effect,value,basis,p,null,query);}
 void Rate(string perk,PassiveEffects effect,string item,float multiplier,string tags=""){
  Perk(perk,false);float before=Value(effect,item,tags);Perk(perk,true);float after=Value(effect,item,tags);Check(before>0&&Math.Abs(after-before*multiplier)<.02f,perk+" native "+effect+" "+before+" -> "+after);Perk(perk,false);
 }
 void Armor(string set,int count){for(int i=0;i<p.equipment.GetSlotCount();i++)p.equipment.SetSlotItem(i,ItemValue.None);int n=0;foreach(string slot in new[]{"Helmet","Outfit","Gloves","Boots"}){if(n++>=count)break;var item=ItemClass.GetItem("armorDelve"+set+slot,false);p.equipment.SetSlotItem((int)((ItemClassArmor)item.ItemClass).EquipSlot,item);}}
 IEnumerator RankChecks(){
  Check(!p.IsDead(),"native living client");
  // XML passives clamp to native rank/prerequisite eligibility, unlike direct
  // custom-handler queries. Prepare a valid trained blade for this comparison.
  float bladePractice=CharacterProgression.Get(p,"delvePracticeBlades"),bladeRank=CharacterProgression.Get(p,"delveLevelBlades");
  Perk("BladesBladeFamiliarity",true);Perk("BladesDrawingBlood",true);CharacterProgression.Set(p,"delvePracticeBlades",ProficiencyRules.Threshold(20));CharacterProgression.Set(p,"delveLevelBlades",20);
  Rate("ArcheryQuickDraw",PassiveEffects.ReloadSpeedMultiplier,"delveBorderBow",1.15f);
  Rate("ArcheryPracticedLoading",PassiveEffects.ReloadSpeedMultiplier,"delveForgedCrossbow",1.15f);
  Rate("WandsSwiftCasting",PassiveEffects.RoundsPerMinute,"delveStarterWand",1.15f);
  try{Rate("BladesQuickHands",PassiveEffects.AttacksPerMinute,"delveBoneDagger",1.1f,"primary,bladeSkill");}finally{CharacterProgression.Set(p,"delvePracticeBlades",bladePractice);CharacterProgression.Set(p,"delveLevelBlades",bladeRank);}
  Rate("BluntBrawler",PassiveEffects.AttacksPerMinute,"delveOakCudgel",1.1f,"primary");
  Rate("UnarmedQuickJabs",PassiveEffects.AttacksPerMinute,"delveLeatherKnuckles",1.1f,"primary");
  foreach(string perk in new[]{"BluntBrawler","UnarmedQuickJabs"}){string item=perk.StartsWith("Blunt")?"delveOakCudgel":"delveLeatherKnuckles";float before=Value(PassiveEffects.AttacksPerMinute,item,"secondary");Perk(perk,true);Check(Value(PassiveEffects.AttacksPerMinute,item,"secondary")==before,perk+" excludes heavy action");Perk(perk,false);}
  foreach(string set in new[]{"Heavy","Medium","Light"}){
   string perk=set=="Heavy"?"HeavyArmorReinforcedPlating":set=="Medium"?"MediumArmorReinforcedSeams":"LightArmorOpenChannels";
   var effect=set=="Light"?PassiveEffects.ReloadSpeedMultiplier:PassiveEffects.PhysicalDamageResist;string item=set=="Light"?"delveStarterWand":"";
   Armor(set,2);yield return new WaitForSeconds(.2f);Perk(perk,false);float before=Value(effect,item);Perk(perk,true);Check(Math.Abs(Value(effect,item)-before)<.02f,perk+" inactive with two pieces");
   Armor(set,3);yield return new WaitForSeconds(.2f);Perk(perk,false);before=Value(effect,item);Perk(perk,true);float expected=set=="Light"?before*1.1f:before+(set=="Heavy"?10:6);Check(Math.Abs(Value(effect,item)-expected)<.02f,perk+" active with three pieces");Perk(perk,false);
  }
  Armor("Heavy",3);Perk("HeavyArmorDeepReserves",false);float stamina=Value(PassiveEffects.StaminaMax);float health=p.Health;Perk("HeavyArmorDeepReserves",true);Check(Math.Abs(Value(PassiveEffects.StaminaMax)-stamina-20)<.02f,"Deep Reserves +20 native maximum");Check(p.Health==health,"equipping/perk query does not heal");Perk("HeavyArmorDeepReserves",false);
  Armor("Light",3);Rate("LightArmorFleetStep",PassiveEffects.WalkSpeed,"",1.05f);
  bool swim=p.isSwimming;float water=p.inWaterPercent;Vector3 throttle=p.vp_FPController.m_MotorThrottle,direction=p.moveDirection;bool jump=p.inputWasJump,down=p.inputWasDown,ground=p.onGround;int exhausted=p.swimExhaustedTicks;
  try{
   p.isSwimming=true;p.inWaterPercent=1;p.onGround=false;p.swimExhaustedTicks=0;p.inputWasJump=false;p.inputWasDown=false;p.moveDirection=Vector3.forward;
   Perk("AthleticsStrongStroke",false);p.vp_FPController.m_MotorThrottle=Vector3.zero;for(int i=0;i<500;i++)p.SwimModeUpdateThrottle();Vector3 normal=p.vp_FPController.m_MotorThrottle;
   Perk("AthleticsStrongStroke",true);p.vp_FPController.m_MotorThrottle=Vector3.zero;for(int i=0;i<500;i++)p.SwimModeUpdateThrottle();Check((p.vp_FPController.m_MotorThrottle-normal*1.15f).magnitude<.0001f,"Strong Stroke stable forward speed over500 native ticks");
   p.moveDirection=Vector3.zero;p.inputWasDown=true;Perk("AthleticsStrongStroke",false);p.vp_FPController.m_MotorThrottle=Vector3.zero;for(int i=0;i<500;i++)p.SwimModeUpdateThrottle();normal=p.vp_FPController.m_MotorThrottle;
   Perk("AthleticsStrongStroke",true);p.vp_FPController.m_MotorThrottle=Vector3.zero;for(int i=0;i<500;i++)p.SwimModeUpdateThrottle();Check((p.vp_FPController.m_MotorThrottle-normal*1.15f).magnitude<.0001f,"Strong Stroke stable vertical speed over500 native ticks");
   Perk("AthleticsStrongStroke",false);Perk("AthleticsLongStride",false);p.vp_FPController.m_MotorThrottle=Vector3.zero;for(int i=0;i<500;i++)p.SwimModeUpdateThrottle();normal=p.vp_FPController.m_MotorThrottle;Perk("AthleticsLongStride",true);p.vp_FPController.m_MotorThrottle=Vector3.zero;for(int i=0;i<500;i++)p.SwimModeUpdateThrottle();Check((p.vp_FPController.m_MotorThrottle-normal).magnitude<.0001f,"Long Stride excludes native swimming");
  }finally{p.isSwimming=swim;p.inWaterPercent=water;p.vp_FPController.m_MotorThrottle=throttle;p.moveDirection=direction;p.inputWasJump=jump;p.inputWasDown=down;p.onGround=ground;p.swimExhaustedTicks=exhausted;}
  report.AppendLine("SCOPE native stat/equipment/swimming paths; input and collision testing deferred.");
 }
}

