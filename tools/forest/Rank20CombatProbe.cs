using System;using System.Collections.Generic;using UnityEngine;using Delve;
public class ConsoleCmdRank20CombatProbe:ConsoleCmdAbstract {
 int checks;EntityPlayerLocal player;World world;
 void Check(bool ok,string name){checks++;if(!ok)throw new Exception(name);}
 void Perk(string skill,string name,bool enabled){player.Progression.GetProgressionValue("delvePerk"+skill+name).Level=enabled?1:0;}
 int Hit(string item,bool heavy){
  var enemy=EntityFactory.CreateEntity(EntityClass.FromString("delveCorruptedWalker"),new Vector3(0,200,3)) as EntityAlive;enemy.world=world;world.Entities.Add(enemy.entityId,enemy);
  try{int health=enemy.Health;var source=new DamageSourceEntity(EnumDamageSource.External,EnumDamageTypes.Slashing,player.entityId);source.AttackingItem=ItemClass.GetItem(item,false);source.SetIgnoreConsecutiveDamages(true);FirstTierCombat.Current=new FirstTierCombat.Swing{Player=player,Heavy=heavy,Skill=Rank20.Skill(source.AttackingItem)};enemy.DamageEntity(source,20,false,0);return health-enemy.Health;}
  finally{FirstTierCombat.Current=null;world.Entities.Remove(enemy.entityId);UnityEngine.Object.Destroy(enemy.gameObject);}
 }
 public override string[] getCommands(){return new[]{"rank20combatverify"};}
 public override string getDescription(){return "Native local-player combat fixture; not multiplayer or human input acceptance.";}
 public override void Execute(List<string> args,CommandSenderInfo sender){try{
  checks=0;world=GameManager.Instance.World;if(GameManager.IsDedicatedServer)throw new Exception("Local-player fixture requires a client process; dedicated servers do not initialize local player input/UI services.");if(world.GetPlayers().Count>0)throw new Exception("Fixture requires no connected players");
  var creation=EntityFactory.SetupEntityCreationData(EntityClass.FromString("playerMale"),new Vector3(0,200,0));creation.belongsPlayerId=creation.id;creation.playerProfile=new PlayerProfile();
  player=EntityFactory.CreateEntity(creation) as EntityPlayerLocal;Check(player!=null,"native local-player factory");player.world=world;player.enabled=false;world.Entities.Add(player.entityId,player);
  int plain=Hit("delveBoneDagger",true);Check(plain>0,"baseline native damage");Perk("Blades","PowerfulCuts",true);Check(Math.Abs(Hit("delveBoneDagger",true)-plain*1.2f)<=1,"heavy blade damage");Check(Hit("delveBoneDagger",false)==plain,"heavy bonus excludes light hits");Perk("Blades","PowerfulCuts",false);
  Perk("Blades","ExploitOpening",true);Check(Math.Abs(Hit("delveBoneDagger",false)-plain*1.2f)<=1,"unaware blade opening");Perk("Blades","ExploitOpening",false);
  Perk("Stealth","OpeningStrike",true);Check(Math.Abs(Hit("delveBoneDagger",false)-plain*1.2f)<=1,"unaware stealth opening");Perk("Stealth","OpeningStrike",false);
  int wand=Hit("delveStarterWand",false);Perk("Wands","MeasuredBolt",true);Check(Math.Abs(Hit("delveStarterWand",false)-wand*1.1f)<=1,"wand direct damage");Perk("Wands","MeasuredBolt",false);
  Perk("Unarmed","PressurePoints",true);Check(Math.Abs(Rank20.Stagger(player,"Unarmed",true)-1.2f)<.001f&&Rank20.Stagger(player,"Unarmed",false)==1,"heavy-only unarmed stagger");Perk("Unarmed","PressurePoints",false);
  Perk("Totems","MendingCurrent",true);Check(Rank20.Healing(player)==1.15f,"mending multiplier");Perk("Totems","MendingCurrent",false);
  var wandItem=ItemClass.GetItem("delveStarterWand",false);float speed=EffectManager.GetValue(PassiveEffects.RoundsPerMinute,wandItem,0,player);Perk("Wands","SwiftCasting",true);Check(Math.Abs(EffectManager.GetValue(PassiveEffects.RoundsPerMinute,wandItem,0,player)-speed*1.15f)<.01f,"native wand fire rate");
  SdtdConsole.Instance.Output("[Rank20Combat] PASS "+checks+" native local-player checks; actual input, hitbox alignment and remote-client behavior remain separate.");
 }catch(Exception ex){SdtdConsole.Instance.Output("[Rank20Combat] FAIL "+ex);}finally{FirstTierCombat.Current=null;if(player!=null){world.Entities.Remove(player.entityId);UnityEngine.Object.Destroy(player.gameObject);}}}
}

