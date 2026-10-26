using HarmonyLib;
using UnityEngine;
using System;
using System.Collections.Generic;
using System.Reflection.Emit;

// Narrow compatibility module for the frozen M3 core. Kept separate so ongoing
// progression work in src/Code cannot silently enter the verified release.
public class DelveSpellVisibilityCompatibility:IModApi
{
    public void InitMod(Mod mod)
    {new Harmony("delve.forged.native-model-visibility").PatchAll(typeof(DelveSpellVisibilityCompatibility).Assembly);}
}
[HarmonyPatch(typeof(Delve.ForgedSpells),"Visible")]
public static class DelveNativeModelVisibility
{
    public static void Postfix(Vector3 from,EntityAlive target,ref bool __result)
    {
        if(__result || target==null)return;
        RaycastHit hit;
        if(Physics.Linecast(from-Origin.position,target.position+Vector3.up-Origin.position,out hit,Physics.DefaultRaycastLayers,QueryTriggerInteraction.Ignore))
            __result=Owns(hit.transform,target.RootTransform) || Owns(hit.transform,target.ModelTransform) || Owns(hit.transform,target.emodel==null?null:target.emodel.GetModelTransform());
    }
    static bool Owns(Transform hit,Transform root){return root!=null && (hit==root || hit.IsChildOf(root));}
    public static bool Owns(Transform hit,EntityAlive entity)
    {return entity!=null && (Owns(hit,entity.RootTransform)||Owns(hit,entity.ModelTransform)||Owns(hit,entity.PhysicsTransform)||Owns(hit,entity.emodel==null?null:entity.emodel.GetModelTransform())||GameUtils.GetHitRootEntity(hit.tag,hit)==entity||CollisionCallForward.FindEntity(hit)==entity);}
    public static bool FromImpact(Vector3 from,EntityAlive target,EntityAlive primary)
    {
        Vector3 delta=target.position+Vector3.up-from;
        var hits=Physics.RaycastAll(from-Origin.position,delta.normalized,delta.magnitude,Physics.DefaultRaycastLayers,QueryTriggerInteraction.Ignore);
        Array.Sort(hits,(a,b)=>a.distance.CompareTo(b.distance));
        foreach(var hit in hits){if(Owns(hit.transform,primary))continue;return Owns(hit.transform,target);}
        return true;
    }
}
[HarmonyPatch(typeof(Delve.ForgedSpells),"BurstTargets")]
public static class DelveImpactVisibility
{
    static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
    {
        int replaced=0;
        var visible=AccessTools.Method(typeof(Delve.ForgedSpells),"Visible");
        foreach(var instruction in instructions) {
            if(instruction.Calls(visible)) {
                var primary=new CodeInstruction(OpCodes.Ldarg_1);primary.labels.AddRange(instruction.labels);primary.blocks.AddRange(instruction.blocks);
                yield return primary;
                yield return new CodeInstruction(OpCodes.Call,AccessTools.Method(typeof(DelveNativeModelVisibility),"FromImpact"));replaced++;
            }else yield return instruction;
        }
        if(replaced!=1)throw new InvalidOperationException("Unexpected frozen M3 impact visibility call count: "+replaced);
    }
}
