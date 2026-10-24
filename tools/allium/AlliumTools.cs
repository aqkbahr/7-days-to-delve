using System;
using System.IO;
using System.Collections.Generic;

// Isolated developer harness. Never shipped as part of the gameplay mod.
public class AlliumTools : IModApi
{
    public void InitMod(Mod mod)
    {
        string worldName = File.ReadAllText(Path.Combine(mod.Path,"world-name.txt")).Trim();
        if(worldName != "Allium-v0.2" && worldName != "Allium-v0.3" && worldName != "Allium-v0.4" && worldName != "Allium-v0.5" && worldName != "Allium-v0.6") throw new InvalidDataException("Unexpected development world");
        string path = Path.GetFullPath(Path.Combine(mod.Path, "../../GeneratedWorlds/"+worldName+"/main.ttw"));
        if (!File.Exists(path) && Directory.Exists(Path.GetDirectoryName(path)))
        {
            WorldState state = new WorldState();
            state.SetFrom(new World(), (EnumChunkProviderId)4);
            state.ResetDynamicData();
            state.seed = 74219;
            if (!state.Save(path)) throw new IOException("Could not create Allium metadata");
            Log.Out("[Allium] Created fresh world metadata " + path);
        }
    }
}
public class ConsoleCmdAlliumProbe : ConsoleCmdAbstract
{
    private static ChunkManager.ChunkObserver observer;
    public override string[] getCommands() { return new[] { "alliumprobe" }; }
    public override string getDescription() { return "Allium developer probe: x z [load], or pois. Load generates test chunks in the isolated save."; }
    public override void Execute(List<string> args, CommandSenderInfo sender)
    {
        try {
            World w = GameManager.Instance.World;
            if(args.Count==1 && args[0]=="pois") {
                List<PrefabInstance> pois=new List<PrefabInstance>();
                w.GetPOIsAtXZ(-4096,4096,-4096,4096,pois);
                SdtdConsole.Instance.Output("[Allium] POI count="+pois.Count);
                foreach(PrefabInstance poi in pois) SdtdConsole.Instance.Output("[Allium] POI "+poi.name+" at "+poi.boundingBoxPosition+" size "+poi.boundingBoxSize);
                return;
            }
            int x = int.Parse(args[0]), z = int.Parse(args[1]);
            if (args.Count > 2 && args[2] == "load") {
                if (observer != null) GameManager.Instance.RemoveChunkObserver(observer);
                observer=GameManager.Instance.AddChunkObserver(new UnityEngine.Vector3(x,80,z),false,3,2);
                SdtdConsole.Instance.Output("[Allium] Requested test chunks; probe again after generation.");
            }
            SdtdConsole.Instance.Output("[Allium] x="+x+" z="+z+" height="+w.GetHeightAt(x,z)+" biome="+w.GetBiomeInWorld(x,z).m_sBiomeName+" water="+w.GetWaterAt(x,z));
            if(w.GetChunkSync(x>>4,z>>4)!=null) {
                int height=w.GetHeight(x,z);
                SdtdConsole.Instance.Output("[Allium] loaded column height="+height+" surface="+w.GetBlock(x,height-1,z).Block.GetBlockName()+" below="+w.GetBlock(x,Math.Max(1,height-6),z).Block.GetBlockName()+" water49="+w.GetWaterPercent(new Vector3i(x,49,z)));
            }
        } catch(Exception ex) { SdtdConsole.Instance.Output("[Allium] ERROR "+ex); }
    }
}

