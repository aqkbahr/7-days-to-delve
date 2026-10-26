using System;using System.IO;using System.Collections.Generic;using System.Reflection;using System.Runtime.Serialization;using UnityEngine;using DelveBatchFiveWorld;
public class ConsoleCmdBatchFiveWorld:ConsoleCmdAbstract {
 static int checks;static void Check(bool b,string s){checks++;if(!b)throw new Exception(s);}
 public override string[] getCommands(){return new[]{"batchfiveworldverify"};}public override string getDescription(){return "Batch 5 world backend, berry, artwork and whole-patch crop verification.";}
 public override void Execute(List<string> args,CommandSenderInfo sender){EntityAlive p=null;try{checks=0;
  p=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),Vector3.zero) as EntityAlive;p.world=GameManager.Instance.World;
  var item=ItemClass.GetItem("foodDelveBrambleberries",false);var ev=new MinEventParams{Self=p,ItemValue=item};
  p.Buffs.SetCustomVar("$foodAmountAdd",0);p.Buffs.SetCustomVar("$waterAmountAdd",0);item.ItemClass.FireEvent(MinEventTypes.onSelfPrimaryActionEnd,ev);
  Check(p.Buffs.GetCustomVar("$foodAmountAdd")==3,"Raw berry food exactly 3: "+p.Buffs.GetCustomVar("$foodAmountAdd"));Check(p.Buffs.GetCustomVar("$waterAmountAdd")==3,"Raw berry water exactly 3");
  foreach(string n in new[]{"menu","wayrest","incursions"}){string path;Check(ModManager.TryPatchModPathString("@modfolder(DelveBatch05World):Textures/"+n+".png",out path)&&File.Exists(path),"Runtime artwork path "+n);Check(new FileInfo(path).Length>100000,"Artwork present "+n);}
  GameObject prefab=null;foreach(var bundle in AssetBundle.GetAllLoadedAssetBundles())if(bundle.name=="batchfiveworld.unity3d")prefab=bundle.LoadAsset<GameObject>("delveIronboundCrate");
  Check(prefab!=null,"Actual native loaded supply crate asset");var col=prefab.GetComponent<BoxCollider>();Check(col!=null&&col.size==Vector3.one&&col.center==new Vector3(0,.5f,0),"Full one-metre interaction collider");var bounds=new Bounds(new Vector3(0,.5f,0),Vector3.zero);foreach(var mesh in prefab.GetComponentsInChildren<MeshFilter>())foreach(var vertex in mesh.sharedMesh.vertices)bounds.Encapsulate(prefab.transform.InverseTransformPoint(mesh.transform.TransformPoint(vertex)));
  Check((bounds.size-Vector3.one).sqrMagnitude<.00001f&&(bounds.center-new Vector3(0,.5f,0)).sqrMagnitude<.00001f,"Visual crate bounds exactly one metre "+bounds);
  int candidates=0,retained=0;var timer=System.Diagnostics.Stopwatch.StartNew();
  for(int seed=0;seed<3;seed++)for(int species=0;species<3;species++){
   var noise=new PerlinNoise(831+seed*197);var sub=(BiomeDefinition)FormatterServices.GetUninitializedObject(typeof(BiomeDefinition));sub.noiseFreq=.055f;sub.noiseMin=0;sub.noiseMax=.22f;sub.noiseOffset=new Vector2(12000+species*1733,19000+species*2357);Check(CropPatches.IsCrop(sub),"Crop selector recognition");
   int before=0,after=0;for(int x=-256;x<256;x++)for(int z=-256;z<256;z++){if(!CropPatches.Inside(noise,sub,x,z))continue;before++;bool keep=CropPatches.Keep(noise,sub,x,z);if(keep)after++;
    if(CropPatches.Inside(noise,sub,x+1,z))Check(keep==CropPatches.Keep(noise,sub,x+1,z),"Whole island preserved horizontally");
    if(CropPatches.Inside(noise,sub,x,z+1))Check(keep==CropPatches.Keep(noise,sub,x,z+1),"Whole island preserved vertically");
   }candidates+=before;retained+=after;
   var provider=(WorldBiomeProviderFromImage)FormatterServices.GetUninitializedObject(typeof(WorldBiomeProviderFromImage));typeof(WorldBiomeProviderFromImage).GetField("noiseGen",BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public).SetValue(provider,noise);var parent=(BiomeDefinition)FormatterServices.GetUninitializedObject(typeof(BiomeDefinition));parent.subbiomes=new List<BiomeDefinition>{sub};var method=typeof(WorldBiomeProviderFromImage).GetMethod("GetSubBiomeIdxAt",BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic);
   for(int x=-40;x<40;x++)for(int z=-40;z<40;z++){bool expected=CropPatches.Inside(noise,sub,x,z)&&CropPatches.Keep(noise,sub,x,z);int actual=(int)method.Invoke(provider,new object[]{parent,x,80,z});Check(actual==(expected?0:-1),"Patched native selector agrees");}
  }
  Check(candidates>1000,"Statistical sample populated");double ratio=(double)retained/candidates;Check(ratio>.40&&ratio<.60,"Approximately half wild patch coverage retained: "+ratio);Check(CropPatches.SafetyFallbacks==0,"No oversized island fallbacks");
  SdtdConsole.Instance.Output("[Batch05World] PASS "+checks+" checks; berries 3/3; one-metre crate mesh/collider; artwork paths; "+retained+"/"+candidates+" crop cells retained ("+(ratio*100).ToString("F2")+"%); whole islands and native selector verified in "+timer.Elapsed.TotalSeconds.ToString("F2")+"s.");
 }catch(Exception e){SdtdConsole.Instance.Output("[Batch05World] FAIL "+e);}finally{if(p!=null)UnityEngine.Object.Destroy(p.gameObject);}}
}
