using System;using System.IO;using System.Text;using System.Collections.Generic;using System.Reflection;using Delve;using UnityEngine;
// Loaded only by the disposable client driver. All temporary perk changes are restored.
public static class ClientFixture {
 public static string Run(){
  var p=GameManager.Instance.World.GetPrimaryPlayer();var report=new StringBuilder();int checks=0;
  var original=new Dictionary<ProgressionValue,int>();
  Action<bool,string> check=(ok,label)=>{if(!ok)throw new Exception(label);checks++;report.AppendLine("PASS "+label);};
  Action<string,bool> perk=(name,on)=>{var value=p.Progression.GetProgressionValue("delvePerk"+name);if(value==null)throw new Exception("Missing perk "+name);if(!original.ContainsKey(value))original.Add(value,value.Level);value.Level=on?1:0;};
  try{
   string folder=GameIO.GetUserGameDataDir(),modePath=Path.Combine(folder,"client-fixture-mode.txt");string mode=File.Exists(modePath)?File.ReadAllText(modePath).Trim():"stats";
   if(mode=="equipment"||mode=="armor"||mode=="effects"||mode=="wraps"||mode=="harvesting"||mode=="performance"||mode=="rank20"||mode=="combat"){new GameObject("DelveAutomatedFixture").AddComponent<EquipmentFixture>().Mode=mode;return "STARTED "+mode+" fixture";}
   if(mode=="inspect-cache"){foreach(var key in AssetBundleManager.Instance.dictAssetBundleRefs.Keys)report.AppendLine(key);report.AppendLine("DROP="+ItemClass.GetItem("delveBoneDagger",false).ItemClass.DropMeshFile);return report.ToString();}
   if(mode=="tutorial"){
    var journal=p.QuestJournal;float award=CharacterProgression.Get(p,"delveTutorialAward"),points=CharacterProgression.Get(p,"delveAttributePoints");int talents=p.Progression.SkillPoints;
    try{p.QuestJournal=new QuestJournal{OwnerPlayer=p};var quest=QuestClass.CreateQuest("delveEmbers");quest.OwnerJournal=p.QuestJournal;p.QuestJournal.quests.Add(quest);check(quest.ID=="delveembers","native lowercased tutorial ID");CharacterProgression.Set(p,"delveTutorialAward",0);int before=CharacterProgression.UnspentAttributes(p);
     p.QuestJournal.CompleteQuest(quest);check(CharacterProgression.UnspentAttributes(p)==before+5,"native tutorial completion grants five attribute points");check(p.Progression.SkillPoints==talents,"tutorial grants no talent points");p.QuestJournal.CompleteQuest(quest);check(CharacterProgression.UnspentAttributes(p)==before+5,"repeated completion does not duplicate entitlement");
     var stream=new MemoryStream();var writer=new PooledBinaryWriter();writer.SetBaseStream(stream);p.QuestJournal.Write(writer);writer.Flush();stream.Position=0;var reader=new PooledBinaryReader();reader.SetBaseStream(stream);var restored=new QuestJournal{OwnerPlayer=p};restored.Read(reader);p.QuestJournal=restored;CharacterProgression.Set(p,"delveTutorialAward",0);CharacterProgression.Initialize(p);check(CharacterProgression.UnspentAttributes(p)==before+5,"native serialized journal recovers lowercased tutorial award");CharacterProgression.Initialize(p);check(CharacterProgression.UnspentAttributes(p)==before+5&&p.Progression.SkillPoints==talents,"recovery remains idempotent and preserves talent budget");return "PASS "+checks+" tutorial native completion/serialization checks\n"+report+"LIMIT: in-process native serialization; full process restart tested separately.";
    }finally{p.QuestJournal=journal;CharacterProgression.Set(p,"delveTutorialAward",award);CharacterProgression.Set(p,"delveAttributePoints",points);p.Progression.SkillPoints=talents;}
   }
   if(mode=="respawn"){XUiC_SpawnSelectionWindow.GetWindow(p.PlayerUI).SpawnButtonPressed(SpawnMethod.NearDeath,-1);return "Requested native test-player respawn";}
   if(mode=="inspect-models"){
    foreach(string name in new[]{"delveBoneDagger","delveOakCudgel","delveAshSpear","delveLeatherKnuckles","delveBorderBow","delveStarterWand","delveStarterStaff","delveStarterTotem","delveForgedBow","delveForgedCrossbow"}){
     var item=ItemClass.GetItem(name,false);if(item==null||item.ItemClass==null){report.AppendLine("MISSING "+name);continue;}string path=item.ItemClass.GetMeshfilePath((BlockShape.MeshPurpose)2,item);report.AppendLine("ITEM "+name+" path="+path);
     var prefab=DataLoader.LoadAsset<GameObject>(path,true);if(prefab==null)continue;foreach(var t in prefab.GetComponentsInChildren<Transform>(true))report.AppendLine("NODE "+t.name+" parent="+(t.parent==null?"-":t.parent.name)+" p="+t.localPosition.ToString("F4")+" r="+t.localEulerAngles.ToString("F3"));foreach(var r in prefab.GetComponentsInChildren<Renderer>(true))report.AppendLine("RENDER "+r.name+" "+r.GetType().Name+" bounds="+r.bounds);
    }File.WriteAllText(Path.Combine(folder,"held-model-inspection.txt"),report.ToString());return "Wrote native held-model inspection";
   }
   if(mode=="verify-death"){
    check(p.IsDead(),"native player death replicated");check(!p.Buffs.HasBuff("delveArborProtected"),"Arbor protection removed by actual player death");bool corpse=false;
    foreach(var target in p.world.EntityAlives)if(EntityClass.GetEntityClassName(target.entityClass)=="delveCorruptedWalker"&&target.IsDead()){corpse=true;check(target.GetComponent("EnemyVisual")!=null,"replicated enemy corpse retains custom visual");}check(corpse,"server enemy death replicated");return "PASS "+checks+" native network death checks\n"+report;
   }
   if(mode=="network-hit"||mode=="network-observe"){
    foreach(var target in p.world.EntityAlives)if(EntityClass.GetEntityClassName(target.entityClass)=="delveCorruptedWalker"&&!target.IsDead()){
     int before=target.Health;Vector3 position=target.position;
     if(mode=="network-hit"){perk("WandsMeasuredBolt",true);var source=new DamageSourceEntity(EnumDamageSource.External,EnumDamageTypes.Slashing,p.entityId);source.AttackingItem=ItemClass.GetItem("delveStarterWand",false);source.SetIgnoreConsecutiveDamages(true);target.DamageEntity(source,20,false,0);}
     return "NETWORK entity="+target.entityId+" before="+before+" after="+target.Health+" position="+position+" playerHealth="+p.Health+" nativeTarget="+(target.GetAttackTarget()==null?-1:target.GetAttackTarget().entityId)+" customVisual="+(target.GetComponent("EnemyVisual")!=null)+"\nLIMIT: direct native damage API, not input or collision acceptance.";
    }throw new Exception("No live isolated Corrupted Walker replicated to client");
   }
   if(mode=="seed-save"){
    int slot=-1;for(int i=p.inventory.SlotCount-1;i>=0;i--)if(p.inventory.GetItem(i).IsEmpty()){slot=i;break;}check(slot>=0,"empty isolated checkpoint slot");
    var food=ItemClass.GetItem("foodDelveTrailRations",false);CraftedProperties.Stamp(food,CraftingManager.GetRecipe("foodDelveTrailRations"),128|Rank20Crafting.Hearty|Rank20Crafting.Trail|Rank20Crafting.Lasting);p.inventory.SetItem(slot,food,2);
    p.Buffs.AddBuff("delveArborProtected");CharacterProgression.Set(p,"delveIntegrationCheckpoint",20261025);
    File.WriteAllText(Path.Combine(folder,"checkpoint-slot.txt"),slot.ToString());return "SEEDED isolated player checkpoint: packed food x2, maker traits, Arbor timer and persistent CVar; slot="+slot;
   }
   if(mode=="verify-save"){
    int slot=int.Parse(File.ReadAllText(Path.Combine(folder,"checkpoint-slot.txt")));var food=p.inventory.GetItem(slot);check(food.count==2,"saved crafted stack count");check(food.itemValue.ItemClass.GetItemName()=="foodDelveTrailRationsDelvePacked","saved packed food identity");check(Rank20Crafting.Marked(food.itemValue,Rank20Crafting.Hearty)&&Rank20Crafting.Marked(food.itemValue,Rank20Crafting.Lasting),"saved maker properties");check(CharacterProgression.Get(p,"delveIntegrationCheckpoint")==20261025,"saved player CVar");check(p.Buffs.HasBuff("delveArborProtected"),"Arbor protection retained on reconnect");var buff=p.Buffs.GetBuff("delveArborProtected");check(buff.DurationInTicks>0&&buff.DurationInTicks<12000,"Arbor timer retained within duration");return "PASS "+checks+" actual reconnect checks\n"+report;
   }
   check(CharacterProgression.IsLocal(p),"real native local player");check(p.world.IsRemote()&&ConnectionManager.Instance.IsConnected,"remote server connection");check(p.PlayerUI!=null,"native player services initialized");
   var wand=ItemClass.GetItem("delveStarterWand",false);perk("WandsSwiftCasting",false);float baseRate=EffectManager.GetValue(PassiveEffects.RoundsPerMinute,wand,0,p);check(baseRate>0,"native wand firing baseline");perk("WandsSwiftCasting",true);check(Math.Abs(EffectManager.GetValue(PassiveEffects.RoundsPerMinute,wand,0,p)-baseRate*1.15f)<.01f,"Swift Casting native firing rate");perk("WandsSwiftCasting",false);
   perk("TotemsMendingCurrent",false);check(Rank20.Healing(p)==1,"untrained healing");perk("TotemsMendingCurrent",true);check(Math.Abs(Rank20.Healing(p)-1.15f)<.001f,"Mending Current healing multiplier");
   perk("UnarmedPressurePoints",true);check(Math.Abs(Rank20.Stagger(p,"Unarmed",true)-1.2f)<.001f,"Pressure Points heavy stagger");check(Rank20.Stagger(p,"Unarmed",false)==1,"Pressure Points excludes light hits");
   var controller=p.vp_FPController;check(controller!=null,"native movement controller");
   float acceleration=controller.MotorAcceleration,damping=controller.MotorDamping,backward=controller.MotorBackwardsSpeed;bool found=false;
   var watch=System.Diagnostics.Stopwatch.StartNew();for(int i=0;i<300;i++)foreach(var state in controller.States)if(state.Name=="Default"&&state.Preset!=null){var a=state.Preset.GetFieldValue("MotorAcceleration");var d=state.Preset.GetFieldValue("MotorDamping");found=a is float&&d is float&&(float)d>0;break;}watch.Stop();
   check(found,"readable native default movement preset");check(controller.MotorAcceleration==acceleration&&controller.MotorDamping==damping&&controller.MotorBackwardsSpeed==backward,"baseline queries preserve native motor values");report.AppendLine("INFO 300 baseline reads: "+watch.Elapsed.TotalMilliseconds+"ms; not a gameplay performance benchmark");
   var held=p.inventory.GetHoldingItemTransform();if(held!=null)foreach(var t in held.GetComponentsInChildren<Transform>(true))report.AppendLine("HELD "+t.name+" local="+t.localPosition);
   return "PASS "+checks+" native client checks\n"+report+"LIMIT: server connection and local API fixtures, not input-driven combat or remote damage acceptance.";
  }catch(Exception ex){return "FAIL after "+checks+" checks\n"+report+ex;}finally{foreach(var entry in original)entry.Key.Level=entry.Value;}
 }
}



