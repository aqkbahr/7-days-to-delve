using System;using System.Collections.Generic;using System.Runtime.CompilerServices;using System.Reflection;using HarmonyLib;
namespace DelveBatchFiveWorld {
 public class ModApi:IModApi {public void InitMod(Mod mod){new Harmony("delve.batch.five.world").PatchAll(Assembly.GetExecutingAssembly());Log.Out("[Batch05World] Whole-patch crop thinning active; presentation and supplies loaded.");}}
 // Keep/discard each entire 8-connected native noise island. Density, species,
 // shape and ground layers of retained patches are unchanged. No POI mutation.
 public static class CropPatches {
  class Cache {public readonly Dictionary<long,bool> Cells=new Dictionary<long,bool>();}
  static readonly object Gate=new object();
  static readonly ConditionalWeakTable<PerlinNoise,Dictionary<BiomeDefinition,Cache>> Caches=new ConditionalWeakTable<PerlinNoise,Dictionary<BiomeDefinition,Cache>>();
  public static int SafetyFallbacks;
  public static bool IsCrop(BiomeDefinition b){int i=((int)b.noiseOffset.x-12000)/1733;return i>=0&&i<21&&Math.Abs(b.noiseFreq-.055f)<.000001&&b.noiseMin==0&&Math.Abs(b.noiseMax-.22f)<.000001&&b.noiseOffset.x==12000+i*1733&&b.noiseOffset.y==19000+i*2357;}
  static long Key(int x,int z){return ((long)x<<32)|(uint)z;}
  public static bool Inside(PerlinNoise n,BiomeDefinition b,int x,int z){double v=(float)n.FBM((double)((float)x+b.noiseOffset.x),(double)((float)z+b.noiseOffset.y),b.noiseFreq);v=v*.5+.5;return v>=b.noiseMin&&v<b.noiseMax;}
  // Batch 9 retains half of Batch 5's surviving islands (one quarter of the
  // original population), using a second hash bit without changing patch size.
  static bool Choose(long anchor,BiomeDefinition b){unchecked{ulong h=(ulong)anchor ^ ((ulong)(uint)b.noiseOffset.x<<17) ^ (uint)b.noiseOffset.y;h^=h>>30;h*=0xbf58476d1ce4e5b9UL;h^=h>>27;h*=0x94d049bb133111ebUL;h^=h>>31;return (h&3)==0;}}
  public static bool Keep(PerlinNoise n,BiomeDefinition b,int x,int z){lock(Gate){
   var dict=Caches.GetOrCreateValue(n);Cache c;if(!dict.TryGetValue(b,out c)){c=new Cache();dict[b]=c;}
   long start=Key(x,z);bool keep;if(c.Cells.TryGetValue(start,out keep))return keep;
   if(c.Cells.Count>200000)c.Cells.Clear();
   var seen=new HashSet<long>();var cells=new List<long>();var queue=new Queue<long>();seen.Add(start);cells.Add(start);queue.Enqueue(start);long anchor=start;
   while(queue.Count>0){long k=queue.Dequeue();int px=(int)(k>>32),pz=(int)k;if(k<anchor)anchor=k;
    for(int dx=-1;dx<=1;dx++)for(int dz=-1;dz<=1;dz++){if(dx==0&&dz==0)continue;int nx=px+dx,nz=pz+dz;long nk=Key(nx,nz);if(!seen.Add(nk)||!Inside(n,b,nx,nz))continue;cells.Add(nk);queue.Enqueue(nk);}
    // Defensive cap for incompatible future noise configurations; never stall generation.
    if(cells.Count>32768){SafetyFallbacks++;return true;}
   }
   keep=Choose(anchor,b);foreach(long k in cells)c.Cells[k]=keep;return keep;
  }}
 }
 [HarmonyPatch(typeof(WorldBiomeProviderFromImage),"GetSubBiomeIdxAt")]
 public static class ThinCrops {static void Postfix(BiomeDefinition __0,int __1,int __3,PerlinNoise ___noiseGen,ref int __result){if(__result<0)return;var b=__0.subbiomes[__result];if(CropPatches.IsCrop(b)&&!CropPatches.Keep(___noiseGen,b,__1,__3))__result=-1;}}
}
