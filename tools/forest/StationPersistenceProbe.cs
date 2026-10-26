using System;
using System.IO;
using System.Xml;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;
public class ConsoleCmdStationPersistence:ConsoleCmdAbstract {
 static EntityPlayer player;static ChunkManager.ChunkObserver observer;
 public override string[] getCommands(){return new[]{"stationpersist"};}
 public override string getDescription(){return "Seed/check 21 placed native stations and saved queues in isolated fixture.";}
 static void Emit(string s){Log.Out(s);SdtdConsole.Instance.Output(s);}
 public override void Execute(List<string> args,CommandSenderInfo sender){
  if(args.Count!=1 || (args[0]!="seed" && args[0]!="check")){Emit("stationpersist seed|check");return;}
  var w=GameManager.Instance.World;
  if(player==null){player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),new Vector3(-2225,240,-1940)) as EntityPlayer;player.world=w;w.Players.Add(player.entityId,player);w.Entities.Add(player.entityId,player);}
  if(observer==null)observer=GameManager.Instance.AddChunkObserver(new Vector3(-2216,80,-1937),false,4,-1);
  GameManager.Instance.StartCoroutine(Run(args[0]));Emit("[StationPersistence] STARTED "+args[0]);
 }
 static IEnumerator Run(string mode){
  var w=GameManager.Instance.World;bool ready=false;
  for(int seconds=0;seconds<120;seconds++){
   ready=true;
   for(int x=-2225;x<=-2207;x+=3)for(int z=-1940;z<=-1934;z+=3){var c=w.GetChunkSync(x>>4,z>>4) as Chunk;if(c==null || !c.IsInitialized || c.InProgressLighting)ready=false;}
   if(ready)break;yield return new WaitForSeconds(1);
  }
  if(!ready){Emit("[StationPersistence] FAIL native readiness timeout");Cleanup();yield break;}
  var mod=ModManager.GetMod("StationProbe",true);string path=Path.Combine(mod.Path,"placed-stations.xml");
  var saved=new XmlDocument();bool prepared=false;var placements=new List<BlockChangeInfo>();
  try{
   if(mode=="seed"){
    var source=new XmlDocument();source.Load(Path.Combine(mod.Path,"slice-checks.xml"));saved.LoadXml("<stations/>");int i=0;
    foreach(XmlElement s in source.SelectNodes("/slice/station")){
     int x=-2225+(i%7)*3,z=-1940+(i/7)*3,y=0;string name=s.GetAttribute("name");
     for(int dx=0;dx<2;dx++)for(int dz=0;dz<2;dz++)y=Math.Max(y,w.GetTerrainHeight(x+dx,z+dz)+1);
     var foundation=new List<BlockChangeInfo>();
     for(int dx=0;dx<2;dx++)for(int dz=0;dz<2;dz++)for(int h=w.GetTerrainHeight(x+dx,z+dz)-1;h<y;h++)foundation.Add(new BlockChangeInfo(new BlockValueRef(new Vector3i(x+dx,h,z+dz)),Block.GetBlockValue("terrStone",false)));
     w.SetBlocksRPC(foundation);
     var n=saved.CreateElement("station");n.SetAttribute("name",name);n.SetAttribute("x",x.ToString());n.SetAttribute("y",y.ToString());n.SetAttribute("z",z.ToString());saved.DocumentElement.AppendChild(n);
     placements.Add(new BlockChangeInfo(new BlockValueRef(new Vector3i(x,y,z)),Block.GetBlockValue(name,false)));i++;
    }
   }else saved.Load(path);
   prepared=true;
  }catch(Exception e){Emit("[StationPersistence] FAIL "+e);}
  if(!prepared){Cleanup();yield break;}
  if(mode=="seed"){yield return new WaitForSeconds(2);w.SetBlocksRPC(placements);}
  yield return new WaitForSeconds(2);
  try{
   int count=0;
   foreach(XmlElement s in saved.SelectNodes("/stations/station")){
    var pos=new Vector3i(int.Parse(s.GetAttribute("x")),int.Parse(s.GetAttribute("y")),int.Parse(s.GetAttribute("z")));string name=s.GetAttribute("name");
    if(w.GetBlock(pos).Block.GetBlockName()!=name)throw new Exception("Placed block mismatch "+name+" at "+pos+" actual="+w.GetBlock(pos).Block.GetBlockName());
    var te=w.GetTileEntity(pos) as TileEntityWorkstation;if(te==null)throw new Exception("Missing workstation tile "+name);
    if(mode=="seed"){
     Recipe recipe=null;foreach(var r in CraftingManager.GetAllRecipes())if(r.craftingArea==name && Delve.ForestSliceCatalog.Rank(r)<=20){recipe=r;break;}
     if(recipe==null)throw new Exception("No tier recipe "+name);
     s.SetAttribute("recipe",Delve.ForestSliceCatalog.Key(recipe));
     te.Output[0]=new ItemStack(ItemClass.GetItem("resourceRockSmall",false),7);
     te.Queue=new[]{new RecipeQueueItem{Recipe=recipe,Multiplier=1,CraftingTimeLeft=50000,OneItemCraftTime=50000,Quality=1,StartingEntityId=-1}};
    }else{
     int stones=0;foreach(var stack in te.Output)if(stack.itemValue.ItemClass!=null && stack.itemValue.ItemClass.GetItemName()=="resourceRockSmall")stones+=stack.count;
     if(stones!=7)throw new Exception("Saved output lost "+name);
     Recipe recipe=null;foreach(var q in te.Queue)if(q!=null && q.Recipe!=null && q.Multiplier>0){recipe=q.Recipe;break;}
     if(recipe==null || Delve.ForestSliceCatalog.Key(recipe)!=s.GetAttribute("recipe"))throw new Exception("Saved recipe variant lost "+name);
     typeof(TileEntityWorkstation).GetMethod("HandleRecipeQueue",BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic).Invoke(te,new object[]{60000f});
     int output=0;foreach(var stack in te.Output)if(stack.itemValue.type==recipe.itemValueType)output+=stack.count;
     if(output!=recipe.count)throw new Exception("Reloaded queue output mismatch "+name);
    }
    count++;
   }
   if(mode=="seed"){saved.Save(path);w.Save();}
   Emit("[StationPersistence] PASS "+mode+" "+count+" placed station identities, stored output and exact queued recipe variants"+(mode=="check"?"; all reloaded queues completed correctly.":"; awaiting process restart."));
  }catch(Exception e){Emit("[StationPersistence] FAIL "+e);}
  Cleanup();
 }
 static void Cleanup(){var w=GameManager.Instance.World;if(observer!=null){GameManager.Instance.RemoveChunkObserver(observer);observer=null;}if(player!=null){w.Players.Remove(player.entityId);w.Entities.Remove(player.entityId);UnityEngine.Object.Destroy(player.gameObject);player=null;}}
}
