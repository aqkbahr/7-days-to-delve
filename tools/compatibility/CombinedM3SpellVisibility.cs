using System;
using HarmonyLib;
using UnityEngine;

// Compatibility for the frozen M3 core: keep unrelated development source out.
public class DelveSpellVisibilityCompatibility:IModApi
{
    public void InitMod(Mod mod)
    {new Harmony("delve.forged.combined-visibility").PatchAll(typeof(DelveSpellVisibilityCompatibility).Assembly);}
}
[HarmonyPatch(typeof(Delve.ForgedSpells),"BurstTargets")]
public static class DelveBurstSourceScope
{
    [ThreadStatic] public static EntityAlive Current;
    static void Prefix(EntityAlive primary,out EntityAlive __state){__state=Current;Current=primary;}
    static Exception Finalizer(Exception __exception,EntityAlive __state){Current=__state;return __exception;}
}
[HarmonyPatch(typeof(Delve.ForgedSpells),"Visible")]
public static class DelveNativeModelVisibility
{
    public static void Postfix(Vector3 from,EntityAlive target,ref bool __result)
    {
        if(target==null)return;
        var source=DelveBurstSourceScope.Current;
        if(source==null && __result)return;
        Vector3 start=from-Origin.position,end=target.position+Vector3.up-Origin.position;
        Vector3 delta=end-start;float length=delta.magnitude;
        if(length<=.0001f){__result=true;return;}
        var hits=Physics.RaycastAll(start,delta/length,length,Physics.DefaultRaycastLayers,QueryTriggerInteraction.Ignore);
        Array.Sort(hits,(a,b)=>a.distance.CompareTo(b.distance));
        foreach(var hit in hits){
            // A burst originates inside its primary victim; that victim is not
            // an intervening wall. Only its own colliders are skipped.
            if(source!=null && Owns(hit.transform,source))continue;
            __result=Owns(hit.transform,target);return;
        }
        __result=true;
    }
    static bool Under(Transform hit,Transform root){return root!=null && (hit==root||hit.IsChildOf(root));}
    static bool Owns(Transform hit,EntityAlive entity){
        return Under(hit,entity.RootTransform)||Under(hit,entity.ModelTransform)||Under(hit,entity.PhysicsTransform)
            ||Under(hit,entity.emodel==null?null:entity.emodel.GetModelTransform())
            ||hit.GetComponentInParent<EntityAlive>()==entity
            ||GameUtils.GetHitRootEntity(hit.tag,hit)==entity||CollisionCallForward.FindEntity(hit)==entity;
    }
}
