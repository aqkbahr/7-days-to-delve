using System;
using System.Collections.Generic;
using HarmonyLib;
namespace Delve {
 // The local authoritative world owns the transaction. Remote clients must not
 // mutate another machine's storage; their normal inventory crafting remains intact.
 public static class NearbyCrafting {
  public static XUiC_WorkstationWindowGroup Station;
  public static bool CraftAction;
  public static int CraftQueries,InventoryOnly;
  static readonly List<TEFeatureStorage> empty=new List<TEFeatureStorage>();
  public static bool InRange(int x,int y,int z){return x*x+y*y+z*z<=25;}
  public static bool Accessible(TileEntityComposite te){
   if(te==null||te.IsUserAccessing())return false;
   var storage=te.GetFeature<TEFeatureStorage>();var permission=te.GetFeature<TEFeatureLockable>();
   if(storage==null||!storage.ItemGrid.PlayerOwned)return false;
   if(permission==null||!permission.IsLocked())return true;
   var user=Platform.PlatformManager.InternalLocalUserIdentifier;
   return user!=null&&(permission.IsUserAllowed(user)||permission.IsOwner(user));
  }
  public static List<TEFeatureStorage> Stores(XUi ui) {
   var w=GameManager.Instance.World;
   if(InventoryOnly>0||w==null||w.IsRemote()||Station==null||Station.xui!=ui||Station.WorkstationData==null||Station.WorkstationData.TileEntity==null)return empty;
   var p=Station.WorkstationData.TileEntity.ToWorldPos();var result=new List<TEFeatureStorage>();
   var area=SettlementStorage.Area(w,p,ui.playerUI.entityPlayer);
   if(area!=null){
    for(int cx=area.MinX>>4;cx<=area.MaxX>>4;cx++)for(int cz=area.MinZ>>4;cz<=area.MaxZ>>4;cz++){
     var chunk=w.GetChunkSync(cx,cz) as Chunk;if(chunk==null)continue;
     foreach(var tile in chunk.GetTileEntities().list){var te=tile as TileEntityComposite;if(te!=null&&area.Contains(te.ToWorldPos())&&Accessible(te))result.Add(te.GetFeature<TEFeatureStorage>());}
    }return result;
   }
   for(int x=-5;x<=5;x++)for(int y=-5;y<=5;y++)for(int z=-5;z<=5;z++){
    if(!InRange(x,y,z))continue;
    var te=w.GetTileEntity(p+new Vector3i(x,y,z)) as TileEntityComposite;
    if(Accessible(te))result.Add(te.GetFeature<TEFeatureStorage>());
   }return result;
  }
  static bool Eligible(ItemStack s,ItemValue v){return s!=null&&!s.IsEmpty()&&s.itemValue.type==v.type&&!s.itemValue.HasMods();}
  public static int Count(List<TEFeatureStorage> stores,ItemValue v){int n=0;foreach(var s in stores)for(int i=0;i<s.ItemGrid.Length;i++)if(!s.ItemGrid.IsLocked(i)&&Eligible(s.ItemGrid[i],v))n+=s.ItemGrid[i].count;return n;}
  public static int InventoryCount(XUiM_PlayerInventory inv,ItemValue v){return inv.Backpack.GetItemCount(v,-1,-1,true)+inv.Toolbelt.GetItemCount(v,false,-1,-1,true);}
  public static bool Has(XUiM_PlayerInventory inv,IList<ItemStack> ingredients,int count){var stores=Stores(inv.xui);foreach(var i in ingredients)if(InventoryCount(inv,i.itemValue)+Count(stores,i.itemValue)<i.count*count)return false;return true;}
  public static void Consume(XUiM_PlayerInventory inv,IList<ItemStack> ingredients,int count,IList<ItemStack> removed){
   ConsumeFrom(inv,Stores(inv.xui),ingredients,count,removed);
  }
  public static void ConsumeFrom(XUiM_PlayerInventory inv,List<TEFeatureStorage> stores,IList<ItemStack> ingredients,int count,IList<ItemStack> removed){
   // Validate the entire request before changing any stack.
   var totals=new Dictionary<int,int>();foreach(var i in ingredients){int n;totals.TryGetValue(i.itemValue.type,out n);totals[i.itemValue.type]=checked(n+i.count*count);}
   foreach(var pair in totals){var v=new ItemValue(pair.Key);if(InventoryCount(inv,v)+Count(stores,v)<pair.Value)throw new InvalidOperationException("Insufficient nearby crafting ingredients");}
   foreach(var item in ingredients){
    int need=item.count*count;need-=inv.Backpack.DecItem(item.itemValue,need,true,removed);if(need>0)need-=inv.Toolbelt.DecItem(item.itemValue,need,true,removed);
    foreach(var s in stores){for(int k=0;k<s.ItemGrid.Length&&need>0;k++){
     var stack=s.ItemGrid[k];if(s.ItemGrid.IsLocked(k)||!Eligible(stack,item.itemValue))continue;
     int take=Math.Min(need,stack.count);if(removed!=null)removed.Add(new ItemStack(stack.itemValue.Clone(),take));
     s.ItemGrid.SetItem(k,new ItemStack(stack.itemValue.Clone(),stack.count-take));need-=take;
    }if(need==0)break;}
    if(need!=0)throw new InvalidOperationException("Nearby crafting ingredients changed during transaction");
   }inv.dispatchBackpackItemsChanged();inv.dispatchToolbeltItemsChanged();
  }
 }
 [HarmonyPatch(typeof(XUiC_WorkstationWindowGroup),"OnOpen")]
 public static class NearbyStationOpen{static void Prefix(XUiC_WorkstationWindowGroup __instance){NearbyCrafting.Station=__instance;}}
 [HarmonyPatch(typeof(XUiC_WorkstationWindowGroup),"OnClose")]
 public static class NearbyStationClose{static void Postfix(XUiC_WorkstationWindowGroup __instance){if(NearbyCrafting.Station==__instance)NearbyCrafting.Station=null;}}
 [HarmonyPatch(typeof(ItemActionEntryCraft),"OnActivated")]
 public static class NearbyCraftScope{static void Prefix(){NearbyCrafting.CraftAction=true;}static Exception Finalizer(Exception __exception){NearbyCrafting.CraftAction=false;return __exception;}}
 [HarmonyPatch(typeof(ItemActionEntryCraft),"hasItems")]
 public static class NearbyCraftQuery{static void Prefix(){NearbyCrafting.CraftQueries++;}static Exception Finalizer(Exception __exception){NearbyCrafting.CraftQueries--;return __exception;}}
 [HarmonyPatch]
 public static class NearbyRepairIsolation{
  static IEnumerable<System.Reflection.MethodBase> TargetMethods(){yield return AccessTools.Method(typeof(ItemActionEntryRepair),"OnActivated");yield return AccessTools.Method(typeof(ItemActionEntryRepair),"RefreshEnabled");}
  static void Prefix(){NearbyCrafting.InventoryOnly++;}static Exception Finalizer(Exception __exception){NearbyCrafting.InventoryOnly--;return __exception;}
 }
 [HarmonyPatch(typeof(XUiM_PlayerInventory),"GetAllItemStacks")]
 public static class NearbyStacks{static void Postfix(XUiM_PlayerInventory __instance,ref List<ItemStack> __result){foreach(var s in NearbyCrafting.Stores(__instance.xui))for(int i=0;i<s.ItemGrid.Length;i++)if(!s.ItemGrid.IsLocked(i)&&!s.ItemGrid[i].IsEmpty()&&!s.ItemGrid[i].itemValue.HasMods())__result.Add(s.ItemGrid[i].Clone());}}
 [HarmonyPatch(typeof(XUiM_PlayerInventory),"GetItemCount",new Type[]{typeof(ItemValue)})]
 public static class NearbyCount{static void Postfix(XUiM_PlayerInventory __instance,ItemValue __0,ref int __result){__result+=NearbyCrafting.Count(NearbyCrafting.Stores(__instance.xui),__0);}}
 [HarmonyPatch(typeof(XUiM_PlayerInventory),"HasItems")]
 public static class NearbyHas{static void Postfix(XUiM_PlayerInventory __instance,IList<ItemStack> __0,int __1,ref bool __result){if(!__result&&(NearbyCrafting.CraftAction||NearbyCrafting.CraftQueries>0)&&NearbyCrafting.Stores(__instance.xui).Count>0)__result=NearbyCrafting.Has(__instance,__0,__1);}}
 [HarmonyPatch(typeof(XUiM_PlayerInventory),"RemoveItems")]
 public static class NearbyRemove{static bool Prefix(XUiM_PlayerInventory __instance,IList<ItemStack> __0,int __1,IList<ItemStack> __2){if(!NearbyCrafting.CraftAction||NearbyCrafting.Stores(__instance.xui).Count==0)return true;NearbyCrafting.Consume(__instance,__0,__1,__2);return false;}}
}
