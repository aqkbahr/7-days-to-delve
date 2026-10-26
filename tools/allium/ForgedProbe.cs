using System;
using System.Collections.Generic;
using System.Xml;
using System.IO;
using UnityEngine;
public class ConsoleCmdForgedVerify:ConsoleCmdAbstract
{
    static int checks;
    static ChunkManager.ChunkObserver observer;
    static void Check(bool value,string reason){if(!value)throw new Exception(reason);checks++;}
    public override string[] getCommands(){return new[]{"forgedverify"};}
    public override string getDescription(){return "Validate Forged gear, gates and native spell effects.";}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        var fixtures=new List<EntityAlive>();
        try {
            if(!Delve.Core.VerifyDefinitions().StartsWith("PASS:")){SdtdConsole.Instance.Output("[Forged] Wait for world load.");return;}
            if(args.Count>0 && args[0]=="load") {
                if(observer!=null)GameManager.Instance.RemoveChunkObserver(observer);
                observer=GameManager.Instance.AddChunkObserver(new Vector3(-2225,80,-1940),false,4,4);
                SdtdConsole.Instance.Output("[Forged] Loading native combat fixture chunks.");return;
            }
            checks=0;var doc=new XmlDocument();doc.Load(Path.Combine(ModManager.GetMod("AlliumTools",true).Path,"forged-checks.xml"));
            // Fixed clear air avoids tree/POI colliders above terrain height.
            // Fixtures are checked synchronously and removed before the next simulation tick.
            var world=GameManager.Instance.World;Vector3 origin=new Vector3(-2225,250,-1940);
            var player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),origin) as EntityAlive;fixtures.Add(player);player.world=world;
            foreach(XmlElement row in doc.SelectNodes("/forged/recipe")) {
                string name=row.GetAttribute("name"),skill=row.GetAttribute("skill");var r=CraftingManager.GetRecipe(name);
                Check(r!=null && r.craftingArea==row.GetAttribute("station") && r.count==int.Parse(row.GetAttribute("count")),"recipe "+name);
                Check(Delve.TrainingHooks.CraftedSkill(name,r.craftingArea)==skill,"ownership "+name);
                Delve.CharacterProgression.Set(player,"delvePractice"+skill,Delve.ProficiencyRules.Threshold(19));
                Check(!Delve.RecipeProgression.Allowed(r,player),"locked at 19 "+name);
                Delve.CharacterProgression.Set(player,"delvePractice"+skill,Delve.ProficiencyRules.Threshold(20));
                Check(Delve.RecipeProgression.Allowed(r,player),"unlocked at 20 "+name);
            }
            foreach(XmlElement row in doc.SelectNodes("/forged/equipment")) {
                var item=ItemClass.GetItem(row.GetAttribute("name"),false);
                Check(item.ItemClass.Properties.GetString("RepairTools")==row.GetAttribute("repair"),"repair binding");
                Check(Math.Abs(EffectManager.GetValue(PassiveEffects.DegradationMax,item)-400)<.01,"durability "+row.GetAttribute("name"));
                if(row.HasAttribute("armor"))Check(Math.Abs(EffectManager.GetValue(PassiveEffects.PhysicalDamageResist,item)-float.Parse(row.GetAttribute("armor")))<.01,"armor value");
                if(row.HasAttribute("capacity"))Check(EffectManager.GetValue(PassiveEffects.MagazineSize,item)==int.Parse(row.GetAttribute("capacity")),"magazine size");
            }
            foreach(XmlElement row in doc.SelectNodes("/forged/rune")) {
                var rune=ItemClass.GetItem(row.GetAttribute("name"),false);
                Check(EffectManager.GetValue(PassiveEffects.EntityDamage,rune)==int.Parse(row.GetAttribute("damage")),"rune damage");
                Check(EffectManager.GetValue(PassiveEffects.BlockDamage,rune)==0,"no rune terrain damage");
            }
            player.Health=player.GetMaxHealth()-50;int before=player.Health;
            Delve.ForgedSpells.Heal(player,25,player.entityId);player.Buffs.Tick();
            Check(player.Health==before+25,"native heal pulse: before="+before+" after="+player.Health);
            float armor=EffectManager.GetValue(PassiveEffects.PhysicalDamageResist,null,0,player);
            Delve.ForgedSpells.Ward(player,player.entityId);Delve.ForgedSpells.Ward(player,player.entityId);
            Check(Math.Abs(EffectManager.GetValue(PassiveEffects.PhysicalDamageResist,null,0,player)-armor-8)<.01,"ward refresh does not stack");
            world.SpawnEntityInWorld(player);
            string enemyClass=args.Count>0?args[0]:"zombieArlene";
            var enemy=EntityFactory.CreateEntity(EntityClass.FromString(enemyClass),origin+new Vector3(0,0,2)) as EntityAlive;fixtures.Add(enemy);world.SpawnEntityInWorld(enemy);
            float speed=EffectManager.GetValue(PassiveEffects.RunSpeed,null,1,enemy);
            enemy.Buffs.AddBuff("delveForgedHex",player.entityId);
            Check(Math.Abs(EffectManager.GetValue(PassiveEffects.RunSpeed,null,1,enemy)-speed*.8f)<.01,"hex movement debuff");
            var near=EntityFactory.CreateEntity(EntityClass.FromString(enemyClass),origin+new Vector3(1,0,2)) as EntityAlive;fixtures.Add(near);world.SpawnEntityInWorld(near);
            foreach(var fixture in fixtures)fixture.SetPosition(fixture.position,true);
            Physics.SyncTransforms();
            RaycastHit obstruction;
            if(Physics.Linecast(enemy.position+Vector3.up-Origin.position,near.position+Vector3.up-Origin.position,out obstruction,Physics.DefaultRaycastLayers,QueryTriggerInteraction.Ignore))
                SdtdConsole.Instance.Output("[Forged] Ray hit "+obstruction.transform.name+" tag="+obstruction.transform.tag+" bounds="+obstruction.collider.bounds+" entity="+CollisionCallForward.FindEntity(obstruction.transform)+" target="+near);
            int health=near.Health,primary=enemy.Health,ally=player.Health;
            int hits=Delve.ForgedSpells.BurstTargets(player,enemy,12,new[]{enemy,near,player});
            if(hits==0 && obstruction.transform!=null) {
                string chain="";for(var t=obstruction.transform;t!=null;t=t.parent)chain+=t.name+"/";
                SdtdConsole.Instance.Output("[Forged] Blocker parents="+chain+" root="+near.RootTransform+" model="+near.ModelTransform+" emodel="+(near.emodel==null?null:near.emodel.GetModelTransform()));
            }
            if(near.EntityClass.bIsEnemyEntity)
                Check(near.Health<health,"native splash damage: hits="+hits+", before="+health+", after="+near.Health+", visible="+Delve.ForgedSpells.Visible(enemy.position+Vector3.up,near));
            else Check(near.Health==health && hits==0,"neutral wildlife excluded from splash");
            Check(enemy.Health==primary && player.Health==ally,"no primary double-hit or friendly splash");
            var scope=Type.GetType("DelveBurstSourceScope, DelveSpellVisibility",false);
            if(scope!=null){
                var current=scope.GetField("Current");
                Check(current.GetValue(null)==null,"burst source scope restored");
                bool threw=false;
                try{Delve.ForgedSpells.BurstTargets(player,enemy,12,FailingTargets());}catch(InvalidOperationException){threw=true;}
                Check(threw && current.GetValue(null)==null,"burst source scope restored after exception");
            }
            var wall=new GameObject("ForgedProbeWall");
            try {
                var collider=wall.AddComponent<BoxCollider>();collider.size=new Vector3(.1f,4,4);
                wall.transform.position=(enemy.position+near.position)*.5f+Vector3.up-Origin.position;Physics.SyncTransforms();
                Check(!Delve.ForgedSpells.Visible(enemy.position+Vector3.up,near),"wall blocks spell visibility");
                int blockedHealth=near.Health;
                Delve.ForgedSpells.BurstTargets(player,enemy,12,new[]{near});
                Check(near.Health==blockedHealth,"wall blocks splash damage");
            }finally{UnityEngine.Object.DestroyImmediate(wall);}
            SdtdConsole.Instance.Output("[Forged] PASS "+checks+" engine checks against "+enemyClass+". Native rigs and multiplayer delivery still need human acceptance.");
        }catch(Exception ex){SdtdConsole.Instance.Output("[Forged] FAIL "+ex);}
        finally{foreach(var fixture in fixtures)if(fixture!=null){if(fixture.world!=null && fixture.world.GetEntity(fixture.entityId)==fixture)fixture.world.RemoveEntity(fixture.entityId,EnumRemoveEntityReason.Despawned);else UnityEngine.Object.Destroy(fixture.gameObject);}}
    }
    static IEnumerable<EntityAlive> FailingTargets(){yield return null;throw new InvalidOperationException("scope restoration fixture");}
}
