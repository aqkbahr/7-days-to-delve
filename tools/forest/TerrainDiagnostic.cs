using System;
using System.Collections.Generic;
using System.Reflection;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using HarmonyLib;
public class TerrainDiagnostic:IModApi
{
    public void InitMod(Mod mod){new Harmony("delve.terrain.diagnostic").PatchAll(Assembly.GetExecutingAssembly());}
}
[HarmonyPatch(typeof(Prefab),"CopyIntoLocal")]
public static class TerrainCopyDiagnostic
{
    static Exception Finalizer(Prefab __instance,Vector3i __1,Exception __exception)
    {
        if(__exception==null)return null;
        Log.Out("[TerrainDiagnostic] COPY FAILED prefab="+__instance.location.FileNameNoExtension+" position="+__1+" size="+__instance.size);
        int bad=0;
        for(int y=0;y<__instance.size.y;y++)for(int z=0;z<__instance.size.z;z++)for(int x=0;x<__instance.size.x;x++){
            var b=__instance.GetBlock(x,y,z);
            if(!b.isair && b.Block==null){if(bad++<12)Log.Out("[TerrainDiagnostic] invalid cell="+x+","+y+","+z+" type="+b.type+" raw="+b.rawData);}
        }
        Log.Out("[TerrainDiagnostic] invalid count="+bad);
        return __exception;
    }
}
public class ConsoleCmdTerrainAudit:ConsoleCmdAbstract
{
    public override string[] getCommands(){return new[]{"terrainaudit"};}
    public override string getDescription(){return "Validate cached Forest decoration prefabs, including native rotation.";}
    public override void Execute(List<string> args,CommandSenderInfo sender){
        try{
            int cells=0;
            foreach(string name in new[]{"deco_iron_vein","deco_coal_vein","deco_lead_vein","deco_nitrate_vein","rock_form01","rock_form02"}){
                var p=GameManager.Instance.World.m_PrefabCache.GetPrefab(name,true,true,false,false);
                for(int r=0;r<4;r++){
                    var q=r==0?p:p.Clone(false);if(r>0)q.RotateY(true,r);
                    for(int y=0;y<q.size.y;y++)for(int z=0;z<q.size.z;z++)for(int x=0;x<q.size.x;x++){
                        var b=q.GetBlock(x,y,z);if(!b.isair && b.Block==null)throw new Exception(name+" rotation="+r+" type="+b.type);
                        cells++;
                    }
                }
            }
            SdtdConsole.Instance.Output("[TerrainAudit] PASS six cached decorations, all rotations, "+cells+" cells");
        }catch(Exception e){SdtdConsole.Instance.Output("[TerrainAudit] FAIL "+e);}
    }
}
public class ConsoleCmdTerrainRace:ConsoleCmdAbstract
{
    public override string[] getCommands(){return new[]{"terrainrace"};}
    public override string getDescription(){return "Stress native prefab decoding against sequential reference hashes.";}
    static ulong Fingerprint(Prefab p){
        ulong hash=1469598103934665603UL;
        for(int y=0;y<p.size.y;y++)for(int z=0;z<p.size.z;z++)for(int x=0;x<p.size.x;x++){
            var b=p.GetBlock(x,y,z);
            if(!b.isair && b.Block==null)throw new Exception("Unresolved block type="+b.type);
            unchecked {hash=(hash^b.rawData)*1099511628211UL;hash=(hash^(byte)p.GetDensity(x,y,z))*1099511628211UL;}
        }
        return hash;
    }
    public override void Execute(List<string> args,CommandSenderInfo sender){
        if(args.Count>0 && args[0]=="channels"){
            try {
                var flags=BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;
                var poolType=typeof(Prefab).GetNestedType("CellPool",BindingFlags.Public|BindingFlags.NonPublic);
                var cellsType=typeof(Prefab).GetNestedType("Cells`1",BindingFlags.Public|BindingFlags.NonPublic);
                var types=new[]{typeof(uint),typeof(ushort),typeof(sbyte),typeof(TextureFullArray),typeof(WaterValue)};
                object[] defaults={0U,(ushort)0,(sbyte)127,TextureFullArray.Default,WaterValue.Empty};
                object[] values={1U,(ushort)7,(sbyte)-127,new TextureFullArray(17),new WaterValue(100)};
                for(int t=0;t<types.Length;t++){
                    object sourcePool=Activator.CreateInstance(poolType,true),targetPool=Activator.CreateInstance(poolType,true);
                    try {
                        var ct=cellsType.MakeGenericType(types[t]);
                        object source=Activator.CreateInstance(ct,flags,null,new object[]{1,defaults[t],sourcePool},null);
                        ct.GetMethod("SetData",flags).Invoke(source,new object[]{8,0,0,values[t]});
                        var list=(System.Collections.IList)poolType.GetField("dataList",flags).GetValue(sourcePool);
                        object bytes=list[0];var indexer=bytes.GetType().GetProperty("Item");
                        for(int i=0;i<8;i++)indexer.SetValue(bytes,(byte)255,new object[]{i});
                        object clone=ct.GetMethod("Clone",flags).Invoke(source,new[]{targetPool});
                        for(int x=0;x<12;x++){
                            object cell=ct.GetMethod("GetCell",flags).Invoke(clone,new object[]{x,0,0});
                            bool has=(bool)cell.GetType().GetProperty("HasData",flags).GetValue(cell,null);
                            if(x<8){if(has)throw new Exception(types[t]+" absent slot materialized");}
                            else {
                                if(!has)throw new Exception(types[t]+" populated slot lost");
                                object actual=cell.GetType().GetMethod("Get",flags,null,new[]{poolType,typeof(int),typeof(int)},null).Invoke(cell,new object[]{targetPool,x,0});
                                if(!actual.Equals(x==8?values[t]:defaults[t]))throw new Exception(types[t]+" value/default differs at "+x);
                            }
                        }
                    }finally {poolType.GetMethod("Cleanup",flags).Invoke(sourcePool,null);poolType.GetMethod("Cleanup",flags).Invoke(targetPool,null);}
                }
                SdtdConsole.Instance.Output("[TerrainChannels] PASS all five sparse channels preserve missing slots, populated values, and channel-specific defaults with poisoned header.");
            }catch(Exception e){SdtdConsole.Instance.Output("[TerrainChannels] FAIL "+e);}
            return;
        }
        if(args.Count>0 && args[0]=="clone"){
            try {
                var p=new Prefab();if(!p.Load("rock_form02",true,true,false,false))throw new Exception("Load failed");
                ulong cloneExpected=Fingerprint(p);
                var flags=BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;
                object pool=typeof(Prefab).GetField("cellPool",flags).GetValue(p);
                var list=(System.Collections.IList)pool.GetType().GetField("dataList",flags).GetValue(pool);
                object bytes=list[0];var indexer=bytes.GetType().GetProperty("Item");
                var saved=new byte[8];for(int i=0;i<8;i++){saved[i]=(byte)indexer.GetValue(bytes,new object[]{i});indexer.SetValue(bytes,(byte)255,new object[]{i});}
                try {
                    if(Fingerprint(p)!=cloneExpected)throw new Exception("Reserved-header poison changed valid source cells");
                    for(int i=0;i<20;i++){
                        var q=p.Clone(false);
                        try {if(Fingerprint(q)!=cloneExpected)throw new Exception("Deep clone differs from unchanged source");q.RotateY(true,i%4);Fingerprint(q);}
                        finally {q.Clear();}
                    }
                    SdtdConsole.Instance.Output("[TerrainClone] PASS 20 deep clones/rotations ignore poisoned unused pool header; source unchanged.");
                } finally {for(int i=0;i<8;i++)indexer.SetValue(bytes,saved[i],new object[]{i});p.Clear();}
            }catch(Exception e){SdtdConsole.Instance.Output("[TerrainClone] FAIL "+e);}
            return;
        }
        if(args.Count>0 && args[0]=="faults"){
            try {
                bool threw=false;var reader=MemoryPools.poolBinaryReader.AllocSync(false);
                try {
                    reader.SetBaseStream(new MemoryStream(new byte[0]));
                    typeof(Prefab).GetMethod("readBlockData",BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic).Invoke(new Prefab(),new object[]{reader,(uint)20,null,true});
                }catch(TargetInvocationException e){threw=e.InnerException is EndOfStreamException;}
                finally{((IDisposable)reader).Dispose();}
                if(!threw)throw new Exception("Expected truncated-data exception");
                var task=Task.Factory.StartNew(()=>{var p=new Prefab();return p.Load("rock_form02",true,true,false,false);});
                if(!task.Wait(10000) || !task.Result)throw new Exception("Decoder lock was not released after exception");
                SdtdConsole.Instance.Output("[TerrainRace] PASS decoder exception preserved; another thread can load afterward.");
            }catch(Exception e){SdtdConsole.Instance.Output("[TerrainRace] FAIL "+e);}
            return;
        }
        var names=new[]{"deco_iron_vein","deco_coal_vein","rock_form01","rock_form02","delve_dungeon_cave_06","delve_dungeon_cave_11"};
        var expected=new ulong[names.Length];var errors=new List<string>();int completed=0;
        try{
            for(int i=0;i<names.Length;i++){var p=new Prefab();if(!p.Load(names[i],true,true,false,false))throw new Exception("Sequential load failed "+names[i]);expected[i]=Fingerprint(p);}
            Parallel.For(0,4,worker=>{
                for(int j=0;j<30;j++){
                    int i=(worker+j)%names.Length;
                    try {var p=new Prefab();if(!p.Load(names[i],true,true,false,false))throw new Exception("Load returned false");if(Fingerprint(p)!=expected[i])throw new Exception("Block/density checksum differs");Interlocked.Increment(ref completed);}
                    catch(Exception e){lock(errors){if(errors.Count<12)errors.Add(names[i]+": "+e.Message);}}
                }
            });
            SdtdConsole.Instance.Output("[TerrainRace] "+(completed==120?"PASS":"FAIL")+" "+completed+"/120 concurrent native decodes match sequential blocks/density; "+String.Join("; ",errors.ToArray()));
        }catch(Exception e){SdtdConsole.Instance.Output("[TerrainRace] FAIL "+e);}
    }
}


