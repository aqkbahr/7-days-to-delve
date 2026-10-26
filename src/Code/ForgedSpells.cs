using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;
namespace Delve
{
    public static class ForgedSpells
    {
        public static bool Visible(Vector3 from,EntityAlive target)
        {
            RaycastHit hit;Vector3 point=target.position+Vector3.up;
            // Entity coordinates are absolute; Unity physics uses the floating origin.
            if(!Physics.Linecast(from-Origin.position,point-Origin.position,out hit,Physics.DefaultRaycastLayers,QueryTriggerInteraction.Ignore))return true;
            Transform model=target.emodel==null?null:target.emodel.GetModelTransform();
            if(model!=null && (hit.transform==model || hit.transform.IsChildOf(model)))return true;
            if(target.RootTransform!=null && (hit.transform==target.RootTransform || hit.transform.IsChildOf(target.RootTransform)))return true;
            if(target.ModelTransform!=null && (hit.transform==target.ModelTransform || hit.transform.IsChildOf(target.ModelTransform)))return true;
            // Native body-part colliders may live under a separate physics rig.
            return hit.collider!=null && ((target.PhysicsTransform!=null && (hit.transform==target.PhysicsTransform || hit.transform.IsChildOf(target.PhysicsTransform))) || hit.collider.GetComponentInParent<EntityAlive>()==target || GameUtils.GetHitRootEntity(hit.transform.tag,hit.transform)==target || CollisionCallForward.FindEntity(hit.transform)==target);
        }
        public static EntityAlive SupportTarget(EntityPlayerLocal caster)
        {
            // Cooperative sessions only: never auto-select a PvP opponent.
            int pvp=GamePrefs.GetInt((EnumGamePrefs)Enum.Parse(typeof(EnumGamePrefs),"PlayerKillingMode"));
            if(pvp!=0)return caster;
            Ray ray=caster.GetLookRay();float nearest=12.01f;EntityAlive selected=caster;
            foreach(EntityAlive entity in caster.world.EntityAlives) {
                if(entity==caster || !(entity is EntityPlayer))continue;
                Vector3 offset=entity.position+Vector3.up-ray.origin;float forward=Vector3.Dot(offset,ray.direction);
                float perpendicular=(offset-ray.direction*forward).sqrMagnitude;
                if(forward>=nearest || !ForgedSpellRules.SupportCandidate(true,!entity.IsDead(),forward,perpendicular,true) || !Visible(ray.origin,entity))continue;
                nearest=forward;selected=entity;
            }
            return selected;
        }
        public static int Heal(EntityAlive target,int amount,int casterId)
        {
            if(target==null || target.IsDead() || amount<=0 || target.Health>=target.GetMaxHealth())return 0;
            int before=target.Health;
            // Native synchronized buff execution owns the health change, including on an ally.
            target.Buffs.AddBuff("delveHealPulse"+Math.Max(1,Math.Min(60,amount)),casterId);
            return Math.Max(0,target.Health-before);
        }
        public static void Ward(EntityAlive target,int casterId)
        {if(target!=null && !target.IsDead())target.Buffs.AddBuff("delveProtectiveWard",casterId,true,false,Rank20.Has(target.world.GetEntity(casterId) as EntityAlive,"Totems","LastingWards")?37.5f:30);}
        public static int Burst(EntityAlive caster,EntityAlive primary,int damage)
        {
            if(caster==null || primary==null || caster.world==null)return 0;
            return BurstTargets(caster,primary,damage,new List<EntityAlive>(caster.world.EntityAlives));
        }
        public static int BurstTargets(EntityAlive caster,EntityAlive primary,int damage,IEnumerable<EntityAlive> candidates)
        {
            if(Rank20.Has(caster,"Staffs","Overload"))damage=(int)Math.Round(damage*1.15f);
            int hits=0;Vector3 origin=primary.position+Vector3.up;
            foreach(EntityAlive target in candidates) {
                if(target==null || !ForgedSpellRules.BurstCandidate(!target.IsDead(),target.EntityClass.bIsEnemyEntity,target is EntityPlayer,target==primary,(target.position-primary.position).sqrMagnitude,true) || !VisibleFromImpact(origin,target,primary))continue;
                // No AttackingItem: splash cannot recursively trigger another burst or weapon perk.
                var source=new DamageSourceEntity(EnumDamageSource.Internal,(EnumDamageTypes)Enum.Parse(typeof(EnumDamageTypes),"Heat"),caster.entityId);
                target.DamageEntity(source,damage,false,0);target.Buffs.AddBuff("delveStaffBurst",caster.entityId);hits++;
            }
            primary.Buffs.AddBuff("delveStaffBurst",caster.entityId);return hits;
        }
        public static bool VisibleFromImpact(Vector3 from,EntityAlive target,EntityAlive primary)
        {
            Vector3 delta=target.position+Vector3.up-from;
            var hits=Physics.RaycastAll(from-Origin.position,delta.normalized,delta.magnitude,Physics.DefaultRaycastLayers,QueryTriggerInteraction.Ignore);
            Array.Sort(hits,(a,b)=>a.distance.CompareTo(b.distance));
            foreach(var hit in hits){if(OwnsCollider(primary,hit.transform))continue;return OwnsCollider(target,hit.transform);}
            return true;
        }
        static bool OwnsCollider(EntityAlive entity,Transform hit)
        {
            if(entity==null)return false;
            foreach(var root in new[]{entity.RootTransform,entity.ModelTransform,entity.PhysicsTransform,entity.emodel==null?null:entity.emodel.GetModelTransform()})
                if(root!=null && (hit==root||hit.IsChildOf(root)))return true;
            return GameUtils.GetHitRootEntity(hit.tag,hit)==entity || CollisionCallForward.FindEntity(hit)==entity;
        }
    }
    [HarmonyPatch(typeof(MinEventActionModifyStats),"execute")]
    public static class ForgedHealingPractice
    {
        static void Prefix(MinEventParams __0,out int __state)
        {
            __state=-1;
            if(__0!=null && __0.Self!=null && __0.Buff!=null && __0.Buff.BuffName.StartsWith("delveHealPulse",StringComparison.Ordinal))__state=__0.Self.Health;
        }
        static void Postfix(MinEventParams __0,int __state)
        {
            if(__state<0 || __0.Self.Health<=__state)return;
            var caster=__0.Self.world.GetEntity(__0.Buff.InstigatorId) as EntityPlayerLocal;
            if(CharacterProgression.IsLocal(caster))CharacterProgression.Practice(caster,"Totems",HealingTotemRules.Practice(__0.Self.Health-__state));
        }
    }
    [HarmonyPatch(typeof(EntityAlive),"DamageEntity",new Type[]{typeof(DamageSource),typeof(int),typeof(bool),typeof(float)})]
    public static class StaffBurstContact
    {
        public struct Hit {public int Health;public EntityPlayerLocal Caster;public int Damage;}
        static void Prefix(EntityAlive __instance,DamageSource __0,out Hit __state)
        {
            __state=new Hit();if(__0==null || __0.AttackingItem==null || __instance.IsDead() || __instance is EntityPlayer)return;
            string item=__0.AttackingItem.ItemClass.GetItemName();
            if(item!="delveStaffRune" && item!="delveMooncapStaffRune" && item!="delveEtchedStaffRune" && item!="delveStarterStaff" && item!="delveForgedStaff")return;
            var caster=__instance.world.GetEntity(__0.getEntityId()) as EntityPlayerLocal;
            if(!CharacterProgression.IsLocal(caster))return;
            bool forged=item=="delveEtchedStaffRune" || caster.inventory.holdingItemItemValue.ItemClass.GetItemName()=="delveForgedStaff";
            __state=new Hit{Health=__instance.Health,Caster=caster,Damage=forged?12:6};
        }
        static void Postfix(EntityAlive __instance,Hit __state)
        {if(__state.Caster!=null && __instance.Health<__state.Health)ForgedSpells.Burst(__state.Caster,__instance,__state.Damage);}
    }
}


