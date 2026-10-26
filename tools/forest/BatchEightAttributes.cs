using System;using System.Collections.Generic;using System.Reflection;using System.Runtime.Serialization;using HarmonyLib;using UnityEngine;using Delve;
// A managed local-player data fixture exercises the actual controller methods
// without opening a game window. Rendering and native player lifecycle are excluded.
public class ConsoleCmdBatchEightAttributes:ConsoleCmdAbstract {
 static EntityPlayerLocal fixture;static bool Player(ref EntityPlayerLocal __result){__result=fixture;return false;}
 public override string[] getCommands(){return new[]{"batch8attributes"};}public override string getDescription(){return "Backend attribute selection/purchase regression; no game UI.";}
 static void Check(bool b,string s){if(!b)throw new Exception(s);}
 public override void Execute(List<string> args,CommandSenderInfo sender){EntityAlive owner=null;var harmony=new Harmony("delve.batch8.attribute.fixture");var flags=BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;var getter=typeof(XUiC_ProgressionScreen).GetProperty("Player",flags).GetGetMethod(true);try{
  owner=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),Vector3.zero) as EntityAlive;owner.world=GameManager.Instance.World;
  fixture=(EntityPlayerLocal)FormatterServices.GetUninitializedObject(typeof(EntityPlayerLocal));
  for(Type t=typeof(EntityPlayer);t!=typeof(MonoBehaviour)&&t!=null;t=t.BaseType)foreach(var f in t.GetFields(flags|BindingFlags.DeclaredOnly))if(!f.IsStatic&&f.DeclaringType.IsInstanceOfType(owner))f.SetValue(fixture,f.GetValue(owner));
  fixture.isEntityRemote=false;fixture.Progression.Level=10;fixture.Buffs.SetCustomVar("delveTutorialAward",1);fixture.Buffs.SetCustomVar("delveProgressionVersion",2);
  CharacterProgression.Initialize(fixture);harmony.Patch(getter,new HarmonyMethod(typeof(ConsoleCmdBatchEightAttributes).GetMethod("Player",BindingFlags.Static|BindingFlags.NonPublic)));
  var screen=new XUiC_ProgressionScreen();var type=screen.GetType();type.GetMethod("SelectTab",flags).Invoke(screen,new object[]{0});
  int skill=fixture.Progression.SkillPoints,budget=CharacterProgression.UnspentAttributes(fixture);
  for(int i=0;i<6;i++){type.GetField("attribute",flags).SetValue(screen,i);type.GetMethod("AttributeDetails",flags).Invoke(screen,null);string name=CharacterProgression.Attributes[i],title="",caption="";screen.GetBindingValueInternal(ref title,"dg_detailtitle");screen.GetBindingValueInternal(ref caption,"dg_purchasecaption");Check(title==name&&caption=="Raise "+name,"Selected details for "+name);var v=fixture.Progression.GetProgressionValue("delveAtt"+name);int old=v.Level;type.GetMethod("Buy",flags).Invoke(screen,null);Check(v.Level==old+1,"Selected purchase "+name);Check(fixture.Progression.SkillPoints==skill,"Skill points preserved");Check(CharacterProgression.UnspentAttributes(fixture)==budget-i-1,"One attribute point per purchase");}
  SdtdConsole.Instance.Output("[Batch08Attributes] PASS all six selected attribute details and purchases; six exact attribute points spent; skill points unchanged. Actual controller methods; no UI opened.");
 }catch(Exception e){SdtdConsole.Instance.Output("[Batch08Attributes] FAIL "+e);}finally{harmony.Unpatch(getter,HarmonyPatchType.All,harmony.Id);fixture=null;if(owner!=null)UnityEngine.Object.Destroy(owner.gameObject);}}
}
