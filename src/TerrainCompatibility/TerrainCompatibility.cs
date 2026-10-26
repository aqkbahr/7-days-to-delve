using System;
using System.Reflection;
using System.Threading;
using System.Collections.Generic;
using System.Reflection.Emit;
using HarmonyLib;

namespace DelveTerrainCompatibility
{
    // 3.3 b18 Prefab.readBlockData uses static sharedData and
    // simpleBitStreamReader. Per-PrefabCache locks do not protect loads through
    // other caches or direct Prefab.Load calls. Serialize the actual decoder,
    // leaving file IO, chunk generation and placement outside this lock.
    public class ModApi : IModApi
    {
        public void InitMod(Mod mod)
        {
            new Harmony("delve.terrain.decoder").PatchAll(Assembly.GetExecutingAssembly());
            Log.Out("[DelveTerrain] Native prefab decoder synchronization enabled.");
            Log.Out("[DelveTerrain] Sparse prefab clone guards enabled for five cell channels.");
        }
    }

    // Native Cells<T>.Clone unconditionally copies offset zero for absent
    // sparse cells. Offset zero is a sentinel, not a readable default cell.
    // Leave the destination slot absent, preserving each channel's default.
    [HarmonyPatch]
    public static class SparseCloneGuard
    {
        static IEnumerable<MethodBase> TargetMethods()
        {
            var cells=typeof(Prefab).GetNestedType("Cells`1",BindingFlags.Public|BindingFlags.NonPublic);
            foreach(var type in new[]{typeof(uint),typeof(ushort),typeof(sbyte),typeof(TextureFullArray),typeof(WaterValue)})
                yield return AccessTools.Method(cells.MakeGenericType(type),"Clone");
        }

        static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions,ILGenerator generator,MethodBase original)
        {
            var code=new List<CodeInstruction>(instructions);
            int source=-1,store=-1;
            for(int i=0;i<code.Count;i++){
                var type=code[i].operand as Type;
                if(type==null || type.Name!="Cell" && !type.Name.StartsWith("Cell`"))continue;
                if(code[i].opcode==OpCodes.Ldelem)source=i;
                if(code[i].opcode==OpCodes.Stelem)store=i;
            }
            if(source<0 || store<=source || !(code[source+1].operand is LocalBuilder))
                throw new InvalidOperationException("Unsupported native sparse clone IL: "+original);
            var local=(LocalBuilder)code[source+1].operand;
            var hasData=AccessTools.PropertyGetter(local.LocalType,"HasData");
            if(hasData==null)throw new InvalidOperationException("Missing sparse cell HasData");
            var skip=generator.DefineLabel();code[store+1].labels.Add(skip);
            code.InsertRange(source+2,new[]{new CodeInstruction(OpCodes.Ldloca,local),new CodeInstruction(OpCodes.Call,hasData),new CodeInstruction(OpCodes.Brfalse,skip)});
            return code;
        }
    }

    [HarmonyPatch(typeof(Prefab),"readBlockData")]
    public static class PrefabDecoderGate
    {
        private static readonly object Gate = new object();

        [HarmonyPriority(Priority.First)]
        static void Prefix(out bool __state)
        {
            __state=false;
            Monitor.Enter(Gate);
            __state=true;
        }

        // A finalizer releases the monitor even if the native decoder or a
        // later patch throws. Preserve the exception for the native loader.
        static Exception Finalizer(bool __state,Exception __exception)
        {
            if(__state)Monitor.Exit(Gate);
            return __exception;
        }
    }
}


