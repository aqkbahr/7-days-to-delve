using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;
namespace Delve
{
    public static class SummonRules
    {
        public const float Lifetime=60;
        public static int Health(int rank){return 80+Math.Max(0,Math.Min(100,rank)-1)*2;}
        public static int Damage(int rank){return 6+Math.Max(0,Math.Min(100,rank)-1)/10;}
        public static int Health(int rank,int quality){return (int)Math.Round(Health(rank)*(1+.1f*(Math.Max(1,Math.Min(6,quality))-1)));}
        public static int Damage(int rank,int quality){return (int)Math.Round(Damage(rank)*(1+.1f*(Math.Max(1,Math.Min(6,quality))-1)));}
        public static int Health(int rank,int quality,bool forged,bool bonded){return (int)Math.Round(Health(rank,quality)*(forged?1.25f:1)*(bonded?1.15f:1));}
        public static int Damage(int rank,int quality,bool forged,bool fierce){return (int)Math.Round(Damage(rank,quality)*(forged?1.25f:1)*(fierce?1.2f:1));}
        public static int Incoming(int damage,bool stalwart){return stalwart&&damage>0?Math.Max(1,(int)Math.Round(damage*.85f)):damage;}
        public static bool Rod(string name){return name=="delveSummoningRod" || name=="delveForgedSummoningRod";}
        public static bool Expired(float now,float end,bool ownerAlive,bool bodyAlive){return now>=end || !ownerAlive || !bodyAlive;}
    }
    public class EntityDelveSummon : EntityAnimal
    {
        public int OwnerId=-1,Rank=1,Quality=1;
        public bool Forged,Fierce,Stalwart;
        public float Expires;
        public override bool IsSavedToFile(){return false;}
    }
    public static class Summoning
    {
        static readonly Dictionary<int,int> bodies=new Dictionary<int,int>();
        static readonly Dictionary<int,float> casts=new Dictionary<int,float>();
        public static void Reset(){bodies.Clear();casts.Clear();
            var type=Type.GetType("DelvePresentation.HeldCatalog, DelvePresentation");
            if(type!=null){var items=type.GetField("Items").GetValue(null) as Dictionary<string,string[]>;if(items!=null){items["delveSummoningRod"]=new[]{"delveMendingTotem","heal"};items["delveForgedSummoningRod"]=new[]{"delveForgedMendingTotem","heal"};}}
        }
        public static bool Hostile(EntityAlive target)
        {return target!=null && !target.IsDead() && !(target is EntityPlayer) && !(target is EntityDelveSummon) && !(target is EntityDelveRecruit) && (target is EntityZombie || target is EntityEnemyAnimal || target.EntityClass.bIsEnemyEntity);}
        public static bool FindSpot(EntityPlayer owner,out Vector3 spot)
        {
            var world=owner.world;var at=owner.GetBlockPosition();
            foreach(var offset in new[]{new Vector3i(2,0,0),new Vector3i(-2,0,0),new Vector3i(0,0,2),new Vector3i(0,0,-2),new Vector3i(1,0,1),new Vector3i(-1,0,-1)})
            for(int y=1;y>=-2;y--){var p=at+offset+new Vector3i(0,y,0);
                if(world.GetChunkSync(p.x>>4,p.z>>4)==null || world.IsWithinTraderArea(p))continue;
                if(world.GetBlock(p).isair && world.GetBlock(p+new Vector3i(0,1,0)).isair && !world.GetBlock(p+new Vector3i(0,-1,0)).isair){
                    spot=p.ToVector3()+new Vector3(.5f,0,.5f);
                    RaycastHit hit;if(!Physics.Linecast(owner.position+Vector3.up-Origin.position,spot+Vector3.up-Origin.position,out hit,Physics.DefaultRaycastLayers,QueryTriggerInteraction.Ignore))return true;
                }
            }
            spot=Vector3.zero;return false;
        }
        public static EntityDelveSummon Cast(EntityPlayer owner)
        {
            if(!Core.IsServer || owner==null || owner.IsDead() || !SummonRules.Rod(owner.inventory.holdingItemItemValue.ItemClass.GetItemName()))return null;
            float now=Time.time,last;if(casts.TryGetValue(owner.entityId,out last)&&now-last<3)return null;
            casts[owner.entityId]=now;Vector3 spot;if(!FindSpot(owner,out spot))return null;
            return Spawn(owner,spot,owner.inventory.holdingItemItemValue.Quality,owner.inventory.holdingItemItemValue.ItemClass.GetItemName()=="delveForgedSummoningRod");
        }
        public static EntityDelveSummon Spawn(EntityPlayer owner,Vector3 spot,int quality=1,bool forged=false)
        {
            if(!Core.IsServer || owner==null || owner.IsDead())return null;
            int rank=ProficiencyRules.Rank(CharacterProgression.Get(owner,"delvePracticeSummoning"));
            var body=EntityFactory.CreateEntity(EntityClass.FromString("delveSummonedBoar"),spot) as EntityDelveSummon;
            if(body==null)return null;
            body.OwnerId=owner.entityId;body.Rank=rank;body.Quality=Math.Max(1,Math.Min(6,quality));body.Forged=forged;
            body.Fierce=Rank20.Has(owner,"Summoning","FierceCompanion");body.Stalwart=Rank20.Has(owner,"Summoning","StalwartCompanion");
            body.Expires=Time.time+(Rank20.Has(owner,"Summoning","EnduringPact")?75:SummonRules.Lifetime);
            int health=SummonRules.Health(rank,body.Quality,forged,Rank20.Has(owner,"Summoning","PrimalBond"));
            body.Buffs.SetCustomVar("delveSummonHealth",health);
            body.Buffs.AddBuff("delveSummonStats");body.Stats.Health.BaseMax=health;body.Health=health;
            body.SetEntityName("Bound Forest Boar");
            int old;if(bodies.TryGetValue(owner.entityId,out old))owner.world.RemoveEntity(old,EnumRemoveEntityReason.Despawned);
            owner.world.SpawnEntityInWorld(body);bodies[owner.entityId]=body.entityId;return body;
        }
        public static void Tick()
        {
            if(!Core.IsServer)return;var world=GameManager.Instance.World;
            foreach(var pair in new List<KeyValuePair<int,int>>(bodies)){
                var owner=world.GetEntity(pair.Key) as EntityPlayer;var body=world.GetEntity(pair.Value) as EntityDelveSummon;
                if(body==null || SummonRules.Expired(Time.time,body.Expires,owner!=null&&!owner.IsDead()&&owner.Health>0,!body.IsDead()&&body.Health>0)){if(body!=null)world.RemoveEntity(body.entityId,EnumRemoveEntityReason.Despawned);bodies.Remove(pair.Key);continue;}
                if((body.position-owner.position).sqrMagnitude>400){Vector3 spot;if(FindSpot(owner,out spot)){body.SetAttackTarget(null,0);body.SetPosition(spot,true);}continue;}
                EntityAlive chosen=null;float nearest=64;
                foreach(var enemy in new List<EntityAlive>(world.EntityAlives)){
                    if(!Hostile(enemy) || (enemy.position-owner.position).sqrMagnitude>144)continue;
                    float distance=(enemy.position-body.position).sqrMagnitude;
                    if(distance<nearest && ForgedSpells.VisibleFromImpact(body.position+Vector3.up,enemy,body)){nearest=distance;chosen=enemy;}
                }
                body.SetAttackTarget(chosen,200);
                if(chosen!=null){body.ClearInvestigatePosition();if(nearest<=16)chosen.SetAttackTarget(body,200);}
                else if((body.position-owner.position).sqrMagnitude>9)body.SetInvestigatePosition(owner.position,200,false);
                else body.ClearInvestigatePosition();
            }
        }
        public static void Practice(EntityPlayer owner,int amount)
        {
            amount=Math.Min(20,Math.Max(0,amount));if(owner==null || owner.IsDead() || amount==0)return;
            if(CharacterProgression.IsLocal(owner))CharacterProgression.Practice((EntityPlayerLocal)owner,"Summoning",amount);
            else ConnectionManager.Instance.SendPackage(NetPackageManager.GetPackage<NetPackageDelveSummonPractice>().Setup(owner.entityId,amount),false,owner.entityId);
        }
    }
    [HarmonyPatch(typeof(ItemActionRanged),"fireShot")]
    public static class SummoningCast
    {
        static bool Prefix(int __0,ItemActionRanged.ItemActionDataRanged __1,ref bool __2,ref Vector3 __result)
        {
            if(!SummonRules.Rod(__1.invData.itemValue.ItemClass.GetItemName()))return true;
            var caster=__1.invData.holdingEntity;__result=caster.GetLookRay().direction;__2=false;
            if(__0==0 && CharacterProgression.IsLocal(caster)){
                if(Core.IsServer)Summoning.Cast((EntityPlayer)caster);
                else ConnectionManager.Instance.SendToServer(NetPackageManager.GetPackage<NetPackageDelveSummonCast>().Setup(caster.entityId),false);
            }
            return false;
        }
    }
    [HarmonyPatch]
    public static class SummonRechargeRecognition
    {
        static bool Prepare(){return Type.GetType("DelveBatchEleven.RechargeSound, DelveBatchEleven")!=null;}
        static System.Reflection.MethodBase TargetMethod(){return AccessTools.Method(Type.GetType("DelveBatchEleven.RechargeSound, DelveBatchEleven"),"Magic");}
        static void Postfix(ItemValue v,ref bool __result){if(v!=null&&v.ItemClass!=null&&SummonRules.Rod(v.ItemClass.GetItemName()))__result=true;}
    }
    [HarmonyPatch]
    public static class SummonRechargeColor
    {
        static bool Prepare(){return Type.GetType("DelveBatchTen.Magic, DelveBatchTen")!=null;}
        static System.Reflection.MethodBase TargetMethod(){return AccessTools.Method(Type.GetType("DelveBatchTen.Magic, DelveBatchTen"),"Family");}
        static void Postfix(ItemValue v,ref string __result){if(v!=null&&v.ItemClass!=null&&SummonRules.Rod(v.ItemClass.GetItemName()))__result="heal";}
    }
    [HarmonyPatch(typeof(EAIApproachAndAttackTarget),"SetData")]
    public static class SummonEnemyMelee
    {
        static void Postfix(Dictionary<string,string> __0,List<EAIApproachAndAttackTarget.TargetClass> ___targetClasses)
        {string classes;if(___targetClasses!=null && __0.TryGetValue("class",out classes) && classes.Contains("EntityPlayer"))___targetClasses.Add(new EAIApproachAndAttackTarget.TargetClass{type=typeof(EntityDelveSummon),chaseTimeMax=0});}
    }
    [HarmonyPatch(typeof(EntityAlive),"DamageEntity",new Type[]{typeof(DamageSource),typeof(int),typeof(bool),typeof(float)})]
    public static class SummonDamage
    {
        public struct Hit{public EntityDelveSummon Body;public int Before;}
        static bool Prefix(EntityAlive __instance,DamageSource __0,ref int __1,out Hit __state)
        {
            __state=new Hit();if(__0==null)return true;
            var body=__instance.world.GetEntity(__0.getEntityId()) as EntityDelveSummon;
            if(body!=null){if(!Core.IsServer || !Summoning.Hostile(__instance))return false;__1=SummonRules.Damage(body.Rank,body.Quality,body.Forged,body.Fierce);__state=new Hit{Body=body,Before=__instance.Health};}
            var summon=__instance as EntityDelveSummon;
            if(summon!=null){var attacker=__instance.world.GetEntity(__0.getEntityId()) as EntityAlive;if(attacker!=null && !Summoning.Hostile(attacker))return false;if(attacker!=null)__1=SummonRules.Incoming(__1,summon.Stalwart);}
            return true;
        }
        static void Postfix(EntityAlive __instance,Hit __state)
        {if(__state.Body!=null && (__instance.Health<__state.Before || __instance.IsDead())){
            var owner=__instance.world.GetEntity(__state.Body.OwnerId) as EntityPlayer;
            bool killed=__instance.IsDead();
            Summoning.Practice(owner,killed?__state.Before:Math.Min(__state.Before,__state.Before-__instance.Health));
            if(__state.Before>0 && killed && owner!=null && !owner.IsDead())owner.AddKillXP(__instance,ItemClass.GetItem("delveSummoningRod",false),1);
        }}
    }
}
public class NetPackageDelveSummonCast : NetPackage
{
    int player;
    public NetPackageDelveSummonCast Setup(int p){player=p;return this;}
    public override NetPackageDirection PackageDirection{get{return NetPackageDirection.ToServer;}}
    public override void write(PooledBinaryWriter w){base.write(w);w.Write(player);}
    public override void read(PooledBinaryReader r){player=r.ReadInt32();}
    public override void ProcessPackage(World w,GameManager m){if(!w.IsRemote()&&ValidEntityIdForSender(player,true))Delve.Summoning.Cast(w.GetEntity(player) as EntityPlayer);}
}
public class NetPackageDelveSummonPractice : NetPackage
{
    int player,amount;
    public NetPackageDelveSummonPractice Setup(int p,int n){player=p;amount=n;return this;}
    public override NetPackageDirection PackageDirection{get{return NetPackageDirection.ToClient;}}
    public override void write(PooledBinaryWriter w){base.write(w);w.Write(player);w.Write(amount);}
    public override void read(PooledBinaryReader r){player=r.ReadInt32();amount=r.ReadInt32();}
    public override void ProcessPackage(World w,GameManager m){var p=w.GetEntity(player) as EntityPlayerLocal;if(w.IsRemote()&&Delve.CharacterProgression.IsLocal(p)&&amount>0&&amount<=20)Delve.CharacterProgression.Practice(p,"Summoning",amount);}
}
