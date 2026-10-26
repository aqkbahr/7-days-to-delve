using HarmonyLib;
using UnityEngine;

namespace Delve
{
    // The native ranged loop checks/consumes ammunition before fireShot. Keep
    // that loop (and reload/effects), replacing only this tool's damaging ray.
    [HarmonyPatch(typeof(ItemActionRanged),"fireShot")]
    public static class HealingTotem
    {
        public static bool InPulse(EntityAlive caster,EntityAlive target)
        {return caster!=null && target is EntityPlayer && !target.IsDead() && (target.position-caster.position).sqrMagnitude<=1.00001f;}
        public static int Pulse(EntityPlayerLocal caster,int amount)
        {
            var targets=new System.Collections.Generic.List<EntityAlive>(caster.world.EntityAlives);
            targets.Add(caster);
            return PulseTargets(caster,amount,targets);
        }
        public static int PulseTargets(EntityAlive caster,int amount,System.Collections.Generic.IEnumerable<EntityAlive> targets)
        {
            var seen=new System.Collections.Generic.HashSet<int>();int count=0;
            foreach(var target in targets)if(InPulse(caster,target)&&seen.Add(target.entityId)){
                // Synchronized native buffs execute healing on each receiving player.
                // The existing pulse callback awards practice once for actual healing.
                ForgedSpells.Heal(target,amount,caster.entityId);
                target.Buffs.AddBuff("delveMendingGlow",caster.entityId);count++;
            }
            return count;
        }
        public static int Apply(EntityAlive target,int amount)
        {
            if(target==null || target.IsDead()) return 0;
            int before=target.Health;
            int healing=HealingTotemRules.Restore(before,target.GetMaxHealth(),amount);
            if(healing>0) target.AddHealth(healing);
            return System.Math.Max(0,target.Health-before);
        }
        private static bool Prefix(int __0,ItemActionRanged.ItemActionDataRanged __1,ref bool __2,ref Vector3 __result)
        {
            ItemValue item=__1.invData.itemValue;
            if(item==null || item.ItemClass==null)return true;
            string name=item.ItemClass.GetItemName();
            if(name!="delveMendingTotem" && name!="delveForgedMendingTotem" && name!="delveWardTotem")return true;
            EntityAlive caster=__1.invData.holdingEntity;
            __result=caster.GetLookRay().direction;
            __2=false;
            // Other clients replay animation, never a second heal/practice award.
            if(__0==0 && CharacterProgression.IsLocal(caster))
            {
                var player=(EntityPlayerLocal)caster;
                EntityAlive target=name=="delveMendingTotem" ? player : ForgedSpells.SupportTarget(player);
                if(name=="delveWardTotem") {ForgedSpells.Ward(target,player.entityId);return false;}
                int wisdom=player.Progression.GetProgressionValue("delveAttWisdom").CalculatedLevel(player);
                int rank=ProficiencyRules.Rank(CharacterProgression.Get(player,"delvePracticeTotems"));
                int amount=HealingTotemRules.Amount(wisdom,rank);
                if(ProgressionRuntime.Has(player,"Totems","SpiritAttunement"))amount=(int)System.Math.Round(amount*1.1f);
                amount=(int)System.Math.Round(amount*Rank20.Healing(player));
                if(name=="delveForgedMendingTotem")amount=(int)System.Math.Round(ForgedSpellRules.Healing(wisdom,rank,ProgressionRuntime.Has(player,"Totems","SpiritAttunement"))*Rank20.Healing(player));
                amount=(int)System.Math.Round(amount*(1+.10f*(System.Math.Max(1,System.Math.Min(6,(int)item.Quality))-1)));
                Pulse(player,amount);
            }
            // No hit callbacks, block damage, aggro or combat-practice credit.
            return false;
        }
    }
}

