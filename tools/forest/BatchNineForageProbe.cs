using System;using System.IO;using System.Collections.Generic;using System.Reflection;using System.Runtime.Serialization;using UnityEngine;using DelveBatchFiveWorld;
public class ConsoleCmdBatchNineForage:ConsoleCmdAbstract {
 static int checks;static void Check(bool b,string s){checks++;if(!b)throw new Exception(s);}
 public override string[] getCommands(){return new[]{"batch9forage"};}public override string getDescription(){return "Batch 5 world backend, berry, artwork and whole-patch crop verification.";}
 public override void Execute(List<string> args,CommandSenderInfo sender){EntityAlive p=null;try{checks=0;
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
  Check(candidates>1000,"Statistical sample populated");double ratio=(double)retained/candidates;Check(ratio>.20&&ratio<.30,"Approximately one quarter of original / half of Batch 5 patches retained: "+ratio);Check(CropPatches.SafetyFallbacks==0,"No oversized island fallbacks");
  SdtdConsole.Instance.Output("[Batch09Forage] PASS "+checks+" checks; "+retained+"/"+candidates+" crop cells retained ("+(ratio*100).ToString("F2")+"%); whole islands and native selector verified in "+timer.Elapsed.TotalSeconds.ToString("F2")+"s.");
 }catch(Exception e){SdtdConsole.Instance.Output("[Batch09Forage] FAIL "+e);}finally{if(p!=null)UnityEngine.Object.Destroy(p.gameObject);}}
}
