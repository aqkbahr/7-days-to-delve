using System.Collections.Generic;
using UnityEngine;
namespace Delve
{
    public static class TotemHex
    {
        public static void Curse(EntityPlayerLocal caster,EntityAlive target,bool forged)
        {
            if(target.IsDead())return;
            target.Buffs.AddBuff(forged?"delveForgedHex":"delveWither",caster.entityId);
            FirstTierCombat.ApplyWound(caster,target,TotemHexRules.DecayDamage*(ProgressionRuntime.Has(caster,"Totems","SpiritAttunement")?1.1f:1),true);
        }
        public static void Impact(EntityPlayerLocal caster,EntityAlive primary,bool forged)
        {
            Curse(caster,primary,forged);
            SplashTargets(caster,primary,forged,new List<EntityAlive>(caster.world.EntityAlives));
        }
        public static int SplashTargets(EntityPlayerLocal caster,EntityAlive primary,bool forged,IEnumerable<EntityAlive> candidates)
        {
            int count=0;var seen=new HashSet<int>();Vector3 origin=primary.position+Vector3.up;
            foreach(var target in candidates)
            {
                if(target==null || !TotemHexRules.Candidate(!target.IsDead(),target.EntityClass.bIsEnemyEntity,target is EntityPlayer,target==primary,(target.position-primary.position).sqrMagnitude) || !seen.Add(target.entityId) || !ForgedSpells.VisibleFromImpact(origin,target,primary))continue;
                // No AttackingItem: secondary damage cannot chain into another splash or award hit perks.
                int before=target.Health;
                target.DamageEntity(new DamageSourceEntity(EnumDamageSource.Internal,EnumDamageTypes.Toxic,caster.entityId),TotemHexRules.SplashDamage(forged),false,0);
                if(target.Health<before){Curse(caster,target,forged);count++;}
            }
            return count;
        }
    }
}
