using System;using System.Collections.Generic;using System.Reflection;using HarmonyLib;using UnityEngine;using Delve;
namespace DelveBatchTen {
 public static class Scythe {
  [ThreadStatic]public static bool Sweeping;
  public static bool Is(ItemValue v){return v!=null&&v.ItemClass!=null&&v.ItemClass.GetItemName()=="delveHarvestScythe";}
  public static float Bonus(int quality){return (Math.Max(1,Math.Min(6,quality))-1)*.1f;}
  public static bool Eligible(BlockValue b){if(b.isair||b.ischild||b.Block is BlockModelTree)return false;string n=b.Block.GetBlockName();return n.StartsWith("grass",StringComparison.OrdinalIgnoreCase)||n.Contains("3Harvest")||n.StartsWith("planted")&&!(b.Block is BlockPlantGrowing);}
  public static bool InArc(Vector3 forward,Vector3 delta){forward.y=0;delta.y=0;float d=delta.magnitude;return d<=2.5f&&d>.15f&&Vector3.Dot(forward.normalized,delta/d)>=.5f&&Mathf.Abs(Vector3.Cross(forward.normalized,delta).y)<=1.5f;}
  public static void Sweep(object[] args){if(Sweeping||!Is(args[21] as ItemValue))return;var p=GameManager.Instance.World.GetEntity((int)args[1]) as EntityPlayerLocal;if(!CharacterProgression.IsLocal(p))return;var original=args[0] as WorldRayHitInfo;if(original==null)return;original=original.Clone();Sweeping=true;try{
   Vector3 origin=p.GetLookRay().origin;var center=World.worldToBlockPos(p.position);int harvested=0;
   for(int z=-3;z<=3;z++)for(int x=-3;x<=3;x++)for(int y=0;y<=2;y++){
    var pos=center+new Vector3i(x,y,z);if(original.bHitValid&&pos==original.hit.blockPos)continue;var b=p.world.GetBlock(pos);if(!Eligible(b)||!InArc(p.GetLookRay().direction,pos.ToVector3()+new Vector3(.5f,0,.5f)-p.position))continue;
    Vector3 point=pos.ToVector3()+new Vector3(.5f,.35f,.5f);var ray=new Ray(origin,point-origin);if(!Voxel.Raycast(p.world,ray,(point-origin).magnitude+.4f,Voxel.HM_Melee,0)||Voxel.voxelRayHitInfo.hit.blockPos!=pos)continue;
    if(p.Stamina<1||p.inventory.holdingItemItemValue.UseTimes>=p.inventory.holdingItemItemValue.MaxUseTimes)break;
    var call=(object[])args.Clone();call[0]=Voxel.voxelRayHitInfo.Clone();var details=new ItemActionAttack.AttackHitInfo();call[12]=details;call[3]=1000f;call[4]=0f;
    AccessTools.Method(typeof(ItemActionAttack),"Hit").Invoke(null,call);
    var action=new ItemActionData(p.inventory.holdingItemData,0);action.attackDetails=details;GameUtils.HarvestOnAttack(action,args[17] as Dictionary<string,ItemActionAttack.Bonuses>);
    p.Stamina-=1;p.inventory.holdingItemItemValue.UseTimes+=1;harvested++;
   }
  }finally{Voxel.voxelRayHitInfo.CopyFrom(original);Sweeping=false;}}
 }
 [HarmonyPatch(typeof(ItemActionAttack),"Hit")] public static class SweepHit {
  // Only the center strike can start a sweep; recursive native hits cannot.
  static bool Prefix(object[] __args){if(!Scythe.Is(__args[21] as ItemValue))return true;var h=__args[0] as WorldRayHitInfo;if(h==null||!h.bHitValid)return true;if(ItemActionAttack.GetEntityFromHit(h)!=null)return true;return Scythe.Eligible(ItemActionAttack.GetBlockHit(GameManager.Instance.World,h));}
  static void Postfix(object[] __args){Scythe.Sweep(__args);}
 }
}
