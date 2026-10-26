using System;
namespace Delve {
 public sealed class StorageArea {
  public int MinX,MaxX,MinZ,MaxZ;
  public bool Contains(Vector3i p){return p.x>=MinX&&p.x<=MaxX&&p.z>=MinZ&&p.z<=MaxZ;}
 }
 public static class SettlementStorage {
  public static StorageArea Square(Vector3i center,int radius){return new StorageArea{MinX=center.x-radius,MaxX=center.x+radius,MinZ=center.z-radius,MaxZ=center.z+radius};}
  public static StorageArea Area(World w,Vector3i station,EntityPlayer player){
   var trader=w.GetTraderAreaAt(station);if(trader!=null)return new StorageArea{MinX=trader.Position.x,MaxX=trader.Position.x+trader.PrefabSize.x-1,MinZ=trader.Position.z,MaxZ=trader.Position.z+trader.PrefabSize.z-1};
   var players=GameManager.Instance.persistentPlayers;if(players==null||player==null)return null;var user=players.GetPlayerDataFromEntityID(player.entityId);if(user==null)return null;
   StorageArea best=null;long distance=long.MaxValue;int radius=(GameStats.GetInt(EnumGameStats.LandClaimSize)-1)/2;
   foreach(var owner in players.Players.Values){if(!owner.PrimaryId.Equals(user.PrimaryId)&&!(owner.IsAlly(user)&&player.Party!=null&&player.Party.ContainsMember(owner.EntityId)))continue;if(!w.IsLandProtectionValidForPlayer(owner))continue;
    foreach(var p in owner.GetLandProtectionBlocks()){var a=Square(p,radius);if(!a.Contains(station))continue;var tile=w.GetTileEntity(p);var claim=tile==null?null:tile.GetSelfOrFeature<TEFeatureLandClaim>();if(claim==null||!claim.IsPrimary())continue;long dx=p.x-station.x,dz=p.z-station.z,d=dx*dx+dz*dz;if(d<distance){distance=d;best=a;}}
   }return best;
  }
 }
}
