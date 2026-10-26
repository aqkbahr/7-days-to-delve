using System;
using System.Collections.Generic;
using System.Reflection.Emit;
using HarmonyLib;
using UnityEngine;
namespace Delve
{
    public static class FirstTierCombat
    {
        public sealed class Swing
        {public EntityPlayerLocal Player;public bool Heavy,Hit,Mining;public string Skill;public float Stamina;}
        [ThreadStatic] public static Swing Current;
        static EntityPlayerLocal owner;
        public static readonly ComboState Combo=new ComboState();
        sealed class Wound {public EntityAlive Target;public WoundState State=new WoundState();public bool Hex;}
        static readonly Dictionary<string,Wound> wounds=new Dictionary<string,Wound>();
        public static void ResetOwner(EntityPlayerLocal player)
        {if(owner!=player){owner=player;Combo.Clear();wounds.Clear();}}
        public static void ApplyWound(EntityPlayerLocal p,EntityAlive target,float damage,bool hex)
        {
            ResetOwner(p);string key=target.entityId+":"+hex;Wound wound;
            if(!wounds.TryGetValue(key,out wound) || wound.Target!=target){wound=new Wound{Target=target,Hex=hex};wounds[key]=wound;}
            if(wound.State.Apply(Time.time,damage*(hex&&Rank20.Has(p,"Totems","LingeringMalice")?1.2f:1),hex?0:2))target.Buffs.AddBuff(hex?"delveTotemDecay":"delveBladeWound",p.entityId);
        }
        public static void Tick(EntityPlayerLocal player)
        {
            ResetOwner(player);
            string held=player.inventory.holdingItemItemValue.ItemClass.GetItemName();
            if(player.IsDead() || ProficiencyRules.Identify(held)!="Unarmed" || !ProgressionRuntime.Has(player,"Unarmed","Combination"))Combo.Clear();
            Combo.Expire(Time.time);CharacterProgression.Set(player,"delveComboCount",Combo.Count);
            if(Combo.Count>0){if(!player.Buffs.HasBuff("delveCombo"))player.Buffs.AddBuff("delveCombo");}else player.Buffs.RemoveBuff("delveCombo");
            var remove=new List<string>();
            foreach(var pair in wounds)
            {
                Wound w=pair.Value;
                if(w.Target==null || w.Target.world!=player.world || w.Target.IsDead() || !w.Target.Buffs.HasBuff(w.Hex?"delveTotemDecay":"delveBladeWound")){remove.Add(pair.Key);continue;}
                float duration=w.Hex?5:6;int amount=w.State.Tick(Time.time,duration);
                if(amount>0)
                {
                    var source=new DamageSourceEntity(EnumDamageSource.Internal,w.Hex?EnumDamageTypes.Toxic:EnumDamageTypes.BloodLoss,player.entityId);
                    // No AttackingItem: damage over time cannot retrigger weapon perks or practice.
                    w.Target.DamageEntity(source,amount,false,0);
                }
                if(Time.time>=w.State.Start+duration)remove.Add(pair.Key);
            }
            foreach(string key in remove)wounds.Remove(key);
        }
    }
    [HarmonyPatch(typeof(ItemActionMelee),"OnHoldingUpdate")]
    public static class FirstTierSwing
    {
        public struct State {public FirstTierCombat.Swing Previous,Active;public bool Started;}
        static void Prefix(ItemActionData __0,out State __state)
        {
            __state=new State{Previous=FirstTierCombat.Current};
            var p=__0.invData.holdingEntity as EntityPlayerLocal;
            if(!CharacterProgression.IsLocal(p))return;
            FirstTierCombat.ResetOwner(p);
            __state.Started=((ItemActionMelee.InventoryDataMelee)__0).bAttackStarted;
            __state.Active=new FirstTierCombat.Swing{Player=p,Heavy=__0.indexInEntityOfAction==1,Skill=ProficiencyRules.Identify(__0.invData.itemValue.ItemClass.GetItemName()),Stamina=p.Stamina};
            FirstTierCombat.Current=__state.Active;
        }
        static void Postfix(ItemActionData __0,State __state)
        {
            var s=__state.Active;if(s==null || !__state.Started || ((ItemActionMelee.InventoryDataMelee)__0).bAttackStarted)return;
            if(s.Skill=="Unarmed" && !s.Hit)FirstTierCombat.Combo.Clear();
            if(s.Mining && ProgressionRuntime.Has(s.Player,"Mining","PickHandling"))s.Player.AddStamina(Math.Max(0,s.Stamina-s.Player.Stamina)*.1f);
        }
        static Exception Finalizer(Exception __exception,State __state){FirstTierCombat.Current=__state.Previous;return __exception;}
    }
    [HarmonyPatch(typeof(EntityAlive),"DamageEntity",new Type[]{typeof(DamageSource),typeof(int),typeof(bool),typeof(float)})]
    public static class FirstTierContact
    {
        public struct Hit {public int Before,Damage;public FirstTierCombat.Swing Swing;public EntityPlayerLocal Caster;public bool Hex,Forged;}
        static void Prefix(EntityAlive __instance,DamageSource __0,ref int __1,out Hit __state)
        {
            __state=new Hit();if(__instance.IsDead() || __instance is EntityPlayer || __0==null || __0.AttackingItem==null)return;
            var p=__instance.world.GetEntity(__0.getEntityId()) as EntityPlayerLocal;
            if(!CharacterProgression.IsLocal(p))return;
            var s=FirstTierCombat.Current;
            if(s!=null && s.Player==p && s.Skill=="Unarmed" && !s.Hit && ProgressionRuntime.Has(p,"Unarmed","Combination") && FirstTierCombat.Combo.Finisher(s.Heavy,Time.time))__1=(int)Math.Round(__1*1.25f);
            string weapon=__0.AttackingItem.ItemClass.GetItemName();
            __state=new Hit{Before=__instance.Health,Damage=__1,Swing=s,Caster=p,Hex=weapon=="delveTotemRune" || weapon=="delveMooncapTotemRune" || weapon=="delveStarterTotem" || weapon=="delveForgedTotem" || weapon=="delveEtchedHexRune"};
            if(__state.Hex){__1=TotemHexRules.ImpactDamage(__1);__state.Forged=weapon=="delveEtchedHexRune" || weapon=="delveForgedTotem" || p.inventory.holdingItemItemValue.ItemClass.GetItemName()=="delveForgedTotem";}
        }
        static void Postfix(EntityAlive __instance,Hit __state)
        {
            if(__state.Before<=0 || __instance.Health>=__state.Before)return;
            var s=__state.Swing;var p=__state.Caster;
            if(s!=null && s.Player==p)
            {
                bool first=!s.Hit;s.Hit=true;
                if(first && s.Skill=="Unarmed" && ProgressionRuntime.Has(p,"Unarmed","Combination"))FirstTierCombat.Combo.Hit(s.Heavy,Time.time);
                if(!__instance.IsDead() && s.Skill=="Blades" && ProgressionRuntime.Has(p,"Blades","DrawingBlood") && __instance.HasAnyTags(FastTags<TagGroup.Global>.Parse("zombie,animal,bandit")) && (s.Heavy || UnityEngine.Random.value<.25f))
                {
                    float resistance=EffectManager.GetValue(PassiveEffects.BuffResistance,null,0,__instance,null,FastTags<TagGroup.Global>.Parse("buffInjuryBleeding"));
                    if(UnityEngine.Random.value>=resistance)FirstTierCombat.ApplyWound(p,__instance,__state.Damage*.2f,false);
                }
                if(!__instance.IsDead() && s.Skill=="Polearms" && s.Heavy && ProgressionRuntime.Has(p,"Polearms","CripplingThrust") && UnityEngine.Random.value<.4f)
                    __instance.Buffs.AddBuff("buffInjuryCrippled01",p.entityId);
            }
            if(__state.Hex)TotemHex.Impact(p,__instance,__state.Forged);
        }
    }
    [HarmonyPatch(typeof(EntityAlive),"damageEntityLocal")]
    public static class CrushingImpact
    {
        public static int Stagger(int strength)
        {
            var s=FirstTierCombat.Current;
            float first=s!=null && s.Skill=="Blunt" && ProgressionRuntime.Has(s.Player,"Blunt","CrushingImpact")?1.2f:1;
            return (int)Math.Round(strength*first*Rank20StaggerScope.Multiplier);
        }
        static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> input)
        {
            // Scale only new damage accumulated toward native knee/prone
            // thresholds. Health damage and stun chance remain unchanged.
            bool window=false;int count=0;
            foreach(var code in input)
            {
                if(code.Calls(AccessTools.PropertyGetter(typeof(DamageSource),"CanStun")))window=true;
                if(code.Calls(AccessTools.Method(typeof(EntityAlive),"GetDamageFraction")))window=false;
                yield return code;
                if(window && code.opcode==OpCodes.Ldarg_2){yield return new CodeInstruction(OpCodes.Call,AccessTools.Method(typeof(CrushingImpact),"Stagger"));count++;}
            }
            if(count!=2)throw new InvalidOperationException("Native stagger accumulation changed: "+count);
        }
    }
    [HarmonyPatch(typeof(EntityBuffs),"AddBuff",new Type[]{typeof(string),typeof(int),typeof(bool),typeof(bool),typeof(float)})]
    public static class PreventDuplicateKnifeBleed
    {
        static bool Prefix(string __0)
        {
            var s=FirstTierCombat.Current;
            return !(s!=null && s.Skill=="Blades" && __0.StartsWith("buffInjuryBleeding",StringComparison.Ordinal) && ProgressionRuntime.Has(s.Player,"Blades","DrawingBlood"));
        }
    }
    [HarmonyPatch(typeof(EntityPlayerLocal),"OnUpdateLive")]
    public static class FirstTierCombatTick
    {static void Postfix(EntityPlayerLocal __instance){if(CharacterProgression.IsLocal(__instance))FirstTierCombat.Tick(__instance);}}
}

