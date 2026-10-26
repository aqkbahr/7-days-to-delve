using System;using System.IO;using System.Text;using System.Collections;using System.Collections.Generic;using UnityEngine;using Delve;using DelvePresentation;
public partial class EquipmentFixture:MonoBehaviour {
 public string Mode="equipment";EntityPlayerLocal p;StringBuilder report=new StringBuilder();int checks;string output;ItemStack held;int heldIndex;ItemValue[] armor;bool god,firstPerson;readonly Dictionary<ProgressionValue,int> perks=new Dictionary<ProgressionValue,int>();
 void Check(bool ok,string text){if(!ok)throw new Exception(text);checks++;report.AppendLine("PASS "+text);}
 void Perk(string key,bool enabled){var value=p.Progression.GetProgressionValue("delvePerk"+key);if(value==null)throw new Exception("Missing perk "+key);if(!perks.ContainsKey(value))perks.Add(value,value.Level);value.Level=enabled?1:0;}
 readonly Dictionary<string,float> variables=new Dictionary<string,float>();bool crouchLocked;
 void Variable(string key,float value){if(!variables.ContainsKey(key))variables.Add(key,CharacterProgression.Get(p,key));CharacterProgression.Set(p,key,value);}
 IEnumerator Start(){p=GameManager.Instance.World.GetPrimaryPlayer();output=Path.Combine(GameIO.GetUserGameDataDir(),Mode+"-result.txt");File.WriteAllText(output,"RUNNING");held=p.inventory.GetItem(0).Clone();heldIndex=p.inventory.holdingItemIdx;armor=new ItemValue[p.equipment.GetSlotCount()];for(int i=0;i<armor.Length;i++)armor[i]=p.equipment.GetSlotItem(i).Clone();god=p.IsGodMode.Value;firstPerson=p.bFirstPersonView;p.IsGodMode.Value=true;
  var run=Mode=="equipment"||Mode=="armor"||Mode=="effects"||Mode=="wraps"?Equipment():Mode=="performance"?Performance():Mode=="rank20"?RankChecks():Mode=="combat"?CombatChecks():Harvest();
  while(true){bool more;object current=null;try{more=run.MoveNext();if(more)current=run.Current;}catch(Exception ex){File.WriteAllText(output,"FAIL after "+checks+" checks\n"+report+ex);Cleanup();yield break;}if(!more)break;yield return current;}
  File.WriteAllText(output,"PASS "+checks+" checks\n"+report+"\nLIMIT: native API fixture, not hands-on UI or visual-fit approval.");Cleanup();
 }
 IEnumerator Equipment(){
  Check(!p.IsDead(),"live test player");p.SetFirstPersonView(false,false);yield return new WaitForSeconds(2);
  foreach(var entry in HeldCatalog.Items){
   if(Mode=="armor"||Mode=="effects")continue;
   if(Mode=="wraps"&&entry.Value[1]!="wraps")continue;
   var item=ItemClass.GetItem(entry.Key,false);p.inventory.SetItem(0,item,1);p.inventory.SetHoldingItemIdxNoHolsterTime(0);yield return new WaitForSeconds(.8f);
   var root=p.inventory.GetHoldingItemTransform();Check(root!=null,entry.Key+" native held model");var art=root.GetComponent<HeldVisual>();Check(art!=null&&art.Visual!=null,entry.Key+" custom held model");Check(art.EffectOrigin!=null,entry.Key+" authored effect socket");
   var skins=art.Visual.GetComponentsInChildren<SkinnedMeshRenderer>(true);Check(skins.Length==3,entry.Key+" three LOD skins");foreach(var skin in skins){var mesh=new Mesh();skin.BakeMesh(mesh);Check(mesh.vertexCount>0&&!float.IsNaN(mesh.bounds.size.sqrMagnitude)&&mesh.bounds.size.magnitude<6,entry.Key+" finite skin "+skin.name);Destroy(mesh);}
   Check(root.GetComponentInChildren<Collider>(true)==null||root.GetComponentInChildren<Collider>(true).enabled==false,entry.Key+" held collider disabled");
   string family=entry.Value[1];if(family=="wand"||family=="staff"||family=="hex"||family=="heal"||family=="ward"){
    int before=ForestEffects.Spawned;((ItemActionRanged)p.inventory.GetHoldingPrimary()).onHoldingEntityFired(p.inventory.holdingItemData.actionData[0]);Check(ForestEffects.Spawned==before+1,entry.Key+" native successful-fire effect callback");
   }
   if(family=="wraps"){Transform hand=null,wrap=null;foreach(var t in p.RootTransform.GetComponentsInChildren<Transform>(true))if(t.name=="LeftWeapon")hand=t;foreach(var t in art.Visual.GetComponentsInChildren<Transform>(true))if(t.name=="LeftWrap")wrap=t;Check(hand!=null&&wrap!=null&&(hand.position-wrap.position).magnitude<.01f,entry.Key+" left wrap follows native left-hand attachment");}
   if(entry.Key=="delveBoneDagger"){
    int before=ForestEffects.Spawned;var action=p.inventory.GetHoldingPrimary();var data=p.inventory.holdingItemData.actionData[0];action.ExecuteAction(data,false);Check(ForestEffects.Spawned==before+1,"native melee start emits one sweep");action.ExecuteAction(data,true);
   }
   if(family=="bow"||family=="crossbow"){
    Transform native=null;foreach(var t in root.GetComponentsInChildren<Transform>(true))if(t.name==(family=="bow"?"bowString":"String")&&!t.IsChildOf(art.Visual.transform)){native=t;break;}
    if(native==null&&family=="bow")foreach(var t in root.GetComponentsInChildren<Transform>(true))if(t.name=="ProjectileJoint"&&!t.IsChildOf(art.Visual.transform)){native=t;break;}
    Check(native!=null,entry.Key+" native draw anchor");var meshA=new Mesh();var meshB=new Mesh();skins[0].BakeMesh(meshA);var old=native.localPosition;native.localPosition=old+Vector3.back*.3f;art.SendMessage("LateUpdate");skins[0].BakeMesh(meshB);native.localPosition=old;art.SendMessage("LateUpdate");float distance=0;var a=meshA.vertices;var b=meshB.vertices;for(int i=0;i<a.Length;i++)distance=Math.Max(distance,(a[i]-b[i]).magnitude);Check(distance>.005f,entry.Key+" custom draw skin follows native anchor "+distance);Destroy(meshA);Destroy(meshB);
   }
  }
  if(Mode=="wraps")yield break;
  foreach(string set in new[]{"Light","Medium","Heavy","Padded","ForgedLight","ForgedMedium","ForgedHeavy"})foreach(string slot in new[]{"Helmet","Outfit","Gloves","Boots"}){
   if(Mode=="effects")continue;
   string name="armorDelve"+set+slot;var item=ItemClass.GetItem(name,false);var cls=(ItemClassArmor)item.ItemClass;p.equipment.SetSlotItem((int)cls.EquipSlot,item);((EModelSDCS)p.emodel).GenerateMeshes();yield return new WaitForSeconds(.9f);
   Check(p.equipment.GetSlotItem((int)cls.EquipSlot).type==item.type,name+" native equip slot");SkinnedMeshRenderer custom=null;
   foreach(var skin in p.emodel.modelTransform.GetComponentsInChildren<SkinnedMeshRenderer>(true))if(skin.name==slot+"_LOD0"&&skin.sharedMaterial!=null&&skin.sharedMaterial.name.StartsWith("ForestArmor",StringComparison.Ordinal))custom=skin;
   if(custom==null){report.AppendLine("SDCS="+cls.SDCSData.PrefabName+" part="+cls.SDCSData.PartName);foreach(var skin in p.GetComponentsInChildren<SkinnedMeshRenderer>(true))report.AppendLine("SKIN "+skin.name+" mat="+(skin.sharedMaterial==null?"null":skin.sharedMaterial.name));}
   Check(custom!=null,name+" native SDCS custom skin");Check(custom.rootBone!=null,name+" native root bone");foreach(var bone in custom.bones)if(bone==null)throw new Exception(name+" missing mapped bone");
   var mesh=new Mesh();custom.BakeMesh(mesh);Check(mesh.vertexCount>0&&mesh.bounds.size.magnitude>.02f&&mesh.bounds.size.magnitude<4,name+" bounded worn geometry "+mesh.bounds.size);Destroy(mesh);
   if(slot=="Helmet"){bool face=false;foreach(var skin in p.emodel.modelTransform.GetComponentsInChildren<SkinnedMeshRenderer>(true))if(skin.name=="head"&&skin.sharedMaterial!=null&&skin.sharedMaterial.name.StartsWith("player",StringComparison.Ordinal))face=true;Check(face,name+" open face retains native player head");}
   var first=new Mesh();var second=new Mesh();custom.BakeMesh(first);var joint=custom.bones[0];var rotation=joint.localRotation;joint.localRotation=rotation*Quaternion.Euler(10,0,0);custom.BakeMesh(second);joint.localRotation=rotation;var av=first.vertices;var bv=second.vertices;float motion=0;for(int i=0;i<av.Length;i++)motion=Math.Max(motion,(av[i]-bv[i]).magnitude);Check(motion>.00001f,name+" weighted native joint deforms worn skin");Destroy(first);Destroy(second);
  }
  p.Buffs.AddBuff("delveProtectiveWard");yield return new WaitForSeconds(.25f);Check(p.GetComponent<BuffVisuals>()!=null,"buff visual observer");Check(FindEffect("DelveEffect_fxWardStatus"),"ward effect follows actual buff");p.Buffs.RemoveBuff("delveProtectiveWard");yield return new WaitForSeconds(.25f);Check(!FindEffect("DelveEffect_fxWardStatus"),"ward effect removed with buff");
  p.Buffs.AddBuff("delveTotemDecay");yield return new WaitForSeconds(.25f);Check(FindEffect("DelveEffect_fxHexStatus"),"hex status effect");p.Buffs.RemoveBuff("delveTotemDecay");yield return new WaitForSeconds(.25f);Check(!FindEffect("DelveEffect_fxHexStatus"),"hex cleanup");
  int healthBefore=p.Health;try{p.Health=p.GetMaxHealth()-20;int before=ForestEffects.Spawned;ForgedSpells.Heal(p,6,p.entityId);p.Buffs.Tick();yield return new WaitForSeconds(.2f);Check(p.Health>p.GetMaxHealth()-20,"native forged healing pulse restores health");Check(ForestEffects.Spawned>before,"successful native healing emits pulse");}finally{p.Health=healthBefore;p.Buffs.RemoveBuff("delveHealPulse6");}
  p.inventory.SetItem(0,ItemClass.GetItem("delveBorderBow",false),1);p.inventory.SetHoldingItemIdxNoHolsterTime(0);yield return new WaitForSeconds(.8f);
  var launch=p.inventory.GetHoldingPrimary();var method=typeof(ItemActionLauncher).GetMethod("instantiateProjectile",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic);var arrow=(Transform)method.Invoke(launch,new object[]{p.inventory.holdingItemData.actionData[0],Vector3.zero});arrow.position=p.position-Origin.position+Vector3.up;var shot=arrow.GetComponent<ProjectileMoveScript>();shot.Fire(p.position+Vector3.up,Vector3.up,p,0,0,false);Check(shot.GetComponent<ProjectileTrail>()!=null&&shot.GetComponentInChildren<EffectLease>()!=null,"native bow projectile has authored trail");
  shot.state=ProjectileMoveScript.State.StickyDestroyed;shot.GetComponent<ProjectileTrail>().SendMessage("Update");yield return null;Check(shot.GetComponentInChildren<EffectLease>()==null,"arrow trail removed on impact state");Destroy(shot.gameObject);
  var spare=p.inventory.GetItem(1).Clone();try{
   var wand=ItemClass.GetItem("delveStarterWand",false);wand.Meta=0;p.inventory.SetItem(0,wand,1);p.inventory.SetItem(1,ItemClass.GetItem("delveWandRune",false),100);p.inventory.SetHoldingItemIdxNoHolsterTime(0);yield return new WaitForSeconds(.8f);
   var reload=typeof(ItemActionRanged).GetMethod("CompleteReload",System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance);var action=p.inventory.GetHoldingPrimary();var data=p.inventory.holdingItemData.actionData[0];int before=ForestEffects.Spawned;reload.Invoke(action,new object[]{data});Check(p.inventory.holdingItemItemValue.Meta>0&&ForestEffects.Spawned==before+1,"native successful recharge loads runes and emits effect");before=ForestEffects.Spawned;reload.Invoke(action,new object[]{data});Check(ForestEffects.Spawned==before,"full focus reload does not emit false recharge");
  }finally{p.inventory.SetItem(1,spare);}
 }
 bool FindEffect(string name){foreach(var t in p.GetComponentsInChildren<Transform>(true))if(t.name==name)return true;return false;}
 IEnumerator Performance(){
  yield return new WaitForSeconds(3);var frames=new List<float>();var watch=System.Diagnostics.Stopwatch.StartNew();long memory=GC.GetTotalMemory(false);int accepted=0;
  Check(ForestEffects.Active==0,"clean effect baseline before stress burst");
  foreach(string skill in new[]{"Mining","Farming"}){Variable("delvePractice"+skill,ProficiencyRules.Threshold(20));Variable("delveLevel"+skill,20);}
  foreach(string perk in new[]{"MiningPickHandling","MiningSoundTechnique","FarmingWorkingHands","FarmingCarefulHarvest","MiningOreSense","FarmingGatherersEye"})Perk(perk,true);bool crouch=p.Crouching;crouchLocked=p.CrouchingLocked;p.CrouchingLocked=true;
  for(int i=0;i<128;i++)if(ForestEffects.Spawn("fxSparkImpact",p.position+Vector3.up,p.transform)!=null)accepted++;
  Check(ForestEffects.Active<=ForestEffects.Limit,"global effect cap enforced");Check(accepted==64,"exactly64 effects accepted from128 attempts");
  float until=Time.realtimeSinceStartup+10;while(Time.realtimeSinceStartup<until){p.Crouching=true;frames.Add(Time.unscaledDeltaTime);yield return null;}p.Crouching=crouch;p.CrouchingLocked=crouchLocked;
  watch.Stop();frames.Sort();Check(ForestEffects.Active==0,"transient effects released after burst");Check(frames.Count>=10,"performance sample collected");report.AppendLine("MEASURE frames="+frames.Count+" median_ms="+(frames[frames.Count/2]*1000)+" p95_ms="+(frames[(int)(frames.Count*.95f)]*1000)+" max_ms="+(frames[frames.Count-1]*1000)+" managed_memory_delta="+(GC.GetTotalMemory(false)-memory)+" duration_ms="+watch.ElapsedMilliseconds);
  var senses=p.GetComponent<Rank20Senses>();Check(senses!=null,"native resource scan component active");var fields=System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance;int cursor=(int)typeof(Rank20Senses).GetField("cursor",fields).GetValue(senses);Check(cursor>0,"resource scanner processed native world cells");var markers=(System.Collections.ICollection)typeof(Rank20Senses).GetField("markers",fields).GetValue(senses);Check(markers.Count<=16,"resource marker pool bounded to16");report.AppendLine("SCAN cursor="+cursor+" marker_pool="+markers.Count);
  Perk("MiningOreSense",false);Perk("FarmingGatherersEye",false);senses.SendMessage("Update");int visible=0;foreach(var line in UnityEngine.Object.FindObjectsOfType<LineRenderer>())if(line.name=="DelveVisibleResourceOutline"&&line.enabled)visible++;Check(visible==0,"resource outlines clear when skills disabled");
  report.AppendLine("SCOPE isolated hidden client, 128 attempted particle bursts, max64 live, both resource scan skills active; no crowd or target-hardware FPS certification.");
 }
 IEnumerator Harvest(){
  Perk("FarmingCarefulHarvest",false);Perk("FarmingGreenThumb",true);var item=ItemClass.GetItem("resourceDelveYarrow",false);string carry="delveHarvestCarry_resourceDelveYarrow";float saved=CharacterProgression.Get(p,carry);CharacterProgression.Set(p,carry,0);
  try{int count=0;for(int i=0;i<20;i++){var stack=new ItemStack(item.Clone(),1);QuestEventManager.instance.HarvestedItem(ItemValue.None,stack,Block.GetBlockValue("plantedDelveYarrow3HarvestPlayer",false));count+=stack.count;}Check(count==23,"twenty cultivated herb harvest events yield23");
   var wild=new ItemStack(item.Clone(),20);QuestEventManager.instance.HarvestedItem(ItemValue.None,wild,Block.GetBlockValue("plantedDelveYarrow3Harvest",false));Check(wild.count==20,"Green Thumb excludes wild harvest");
   var seed=new ItemStack(ItemClass.GetItem("plantedDelveYarrow1",false),20);QuestEventManager.instance.HarvestedItem(ItemValue.None,seed,Block.GetBlockValue("plantedDelveYarrow3HarvestPlayer",false));Check(seed.count==20,"seed yield not amplified");
  }finally{CharacterProgression.Set(p,carry,saved);}
  Perk("FarmingCleanButchery",true);
  var corpse=EntityFactory.CreateEntity(EntityClass.FromString("delveThornbackBoar"),p.position+Vector3.down*100) as EntityAlive;
  var previous=HarvestContext.Action;
  try{Check(corpse!=null,"native Thornback corpse fixture");corpse.world=p.world;corpse.SetDead();Check(corpse.IsDead(),"native corpse death state");
   HarvestContext.Action=new ItemActionData(null,0){attackDetails=new ItemActionAttack.AttackHitInfo{entityHit=corpse}};
   foreach(string resource in new[]{"foodRawMeat","resourceAnimalFat","resourceBone","resourceLeather"}){
    string key="delveHarvestCarry_"+resource;float before=CharacterProgression.Get(p,key);CharacterProgression.Set(p,key,0);
    try{int total=0;for(int i=0;i<20;i++){var stack=new ItemStack(ItemClass.GetItem(resource,false),1);QuestEventManager.instance.HarvestedItem(ItemValue.None,stack,BlockValue.Air);total+=stack.count;}Check(total==(resource=="foodRawMeat"||resource=="resourceAnimalFat"?23:20),"Clean Butchery corpse yield "+resource+"="+total);}finally{CharacterProgression.Set(p,key,before);}
   }
   Destroy(corpse.gameObject);corpse=EntityFactory.CreateEntity(EntityClass.FromString("delveThornbackBoar"),p.position+Vector3.down*100) as EntityAlive;corpse.world=p.world;HarvestContext.Action.attackDetails.entityHit=corpse;Check(!corpse.IsDead(),"living animal fixture");var living=new ItemStack(ItemClass.GetItem("foodRawMeat",false),20);QuestEventManager.instance.HarvestedItem(ItemValue.None,living,BlockValue.Air);Check(living.count==20,"Clean Butchery excludes living animals");
  }finally{HarvestContext.Action=previous;if(corpse!=null)Destroy(corpse.gameObject);}
  foreach(string crop in new[]{"Yarrow","Thyme","Mooncap","Bramble"}){var block=Block.GetBlockValue("plantedDelve"+crop+"3HarvestPlayer",false);Check(!block.isair,"cultivated harvest block "+crop);}
  var bag=new ItemStack[p.bag.SlotCount];for(int i=0;i<bag.Length;i++)bag[i]=p.bag.ItemGrid.GetItemClone(i);var belt=new ItemStack[p.inventory.SlotCount];for(int i=0;i<belt.Length;i++)belt[i]=p.inventory.GetItem(i).Clone();
  try{foreach(string crop in new[]{"Yarrow","Thyme","Mooncap","Bramble"}){
   for(int i=0;i<bag.Length;i++)p.bag.SetSlot(i,ItemStack.Empty.Clone());for(int i=0;i<belt.Length;i++)p.inventory.SetItem(i,ItemStack.Empty.Clone());p.inventory.SetItem(0,ItemClass.GetItem("delveBoneDagger",false),1);
   string resource=crop=="Bramble"?"foodDelveBrambleberries":"resourceDelve"+crop;var value=ItemClass.GetItem(resource,false);string key="delveHarvestCarry_"+resource;float old=CharacterProgression.Get(p,key);CharacterProgression.Set(p,key,0);
   try{var block=Block.GetBlockValue("plantedDelve"+crop+"3HarvestPlayer",false);var action=new ItemActionData(p.inventory.GetItemDataInSlot(0),0){attackDetails=new ItemActionAttack.AttackHitInfo{blockBeingDamaged=block,bBlockHit=true,bKilled=true,bHarvestTool=true,damageGiven=block.Block.MaxDamage,damageMax=block.Block.MaxDamage,damageTotalOfTarget=block.Block.MaxDamage,itemsToDrop=block.Block.itemsToDrop}};
    for(int n=0;n<20;n++){action.attackDetails.blockBeingDamaged=block;GameUtils.HarvestOnAttack(action,null);}int count=p.bag.GetItemCount(value);for(int i=0;i<belt.Length;i++){var stack=p.inventory.GetItem(i);if(stack.itemValue.type==value.type)count+=stack.count;}Check(count==46,"native harvest-to-inventory "+crop+" 40base+6bonus="+count);Check(HarvestContext.Action==previous,"native harvest context restored");
   }finally{CharacterProgression.Set(p,key,old);}
  }}finally{p.bag.SetSlots(bag,true);for(int i=0;i<belt.Length;i++)p.inventory.SetItem(i,belt[i]);}
  report.AppendLine("SCOPE native harvest/drop/inventory pipeline and corpse classification; physical tool collision/block destruction deferred.");
  yield return null;
 }
 void Cleanup(){try{foreach(var value in perks)value.Key.Level=value.Value;if(p!=null){foreach(var variable in variables)CharacterProgression.Set(p,variable.Key,variable.Value);if(Mode=="performance")p.CrouchingLocked=crouchLocked;p.inventory.SetItem(0,held);p.inventory.SetHoldingItemIdxNoHolsterTime(heldIndex);for(int i=0;i<armor.Length;i++)p.equipment.SetSlotItem(i,armor[i]);p.IsGodMode.Value=god;p.SetFirstPersonView(firstPerson,false);p.Buffs.RemoveBuff("delveProtectiveWard");p.Buffs.RemoveBuff("delveTotemDecay");}}finally{Destroy(gameObject);}}
}
