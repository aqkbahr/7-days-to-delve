using System;
using System.IO;
using System.Collections.Generic;
using System.Xml;
using HarmonyLib;
using UnityEngine;

namespace DelveForest
{
    public sealed class PoiRule { public int Volume; public string Kind; }
    public class ModApi : IModApi
    {
        public static readonly Dictionary<string,PoiRule> Pois=new Dictionary<string,PoiRule>(StringComparer.OrdinalIgnoreCase);
        public static readonly string[] Roster={"delveCorruptedWalker","delveImp","delvePossessedSoldier","delveDemonSpawn","delveHellhound","delveWarpedBrute","delveThornbackBoar","delveGloomcat","delveCrystalStag"};
        public void InitMod(Mod mod)
        {
            var xml=new XmlDocument();xml.Load(Path.Combine(mod.Path,"ForestEncounters.xml"));Pois.Clear();
            foreach(XmlElement e in xml.SelectNodes("/forest/poi")) Pois.Add(e.GetAttribute("name"),new PoiRule{Volume=int.Parse(e.GetAttribute("volume")),Kind=e.GetAttribute("kind")});
            new Harmony("delve.forest.bestiary").PatchAll(typeof(ModApi).Assembly);
            ModEvents.GameStartDone.RegisterHandler(ForestCampaign.Start);
            ModEvents.GameUpdate.RegisterHandler(ForestCampaign.Update);
            ModEvents.WorldShuttingDown.RegisterHandler(ForestCampaign.Stop);
            Log.Out("[DelveForest] Loaded nine reusable creatures and "+Pois.Count+" Forest POI encounter assignments; Warden uses the existing campaign controller.");
        }
        public static string Replacement(SleeperVolume volume,int stage,int ordinal,int original)
        {
            var poi=volume.PrefabInstance;PoiRule rule;
            if(poi==null || poi.prefab==null || !Pois.TryGetValue(poi.prefab.PrefabName,out rule))return null;
            if(poi.sleeperVolumes==null || poi.sleeperVolumes.IndexOf(volume)!=rule.Volume)return null;
            // Existing custom respawn records retain their identity.
            string name=EntityClass.GetEntityClassName(original);
            if(name!=null && name.StartsWith("delve",StringComparison.Ordinal))return null;
            // Only players actually near the location affect its authored tier.
            // No connected-player fixture falls back to the native-stage rule.
            int level=0;
            var world=GameManager.Instance.World;
            var center=new Vector3(poi.boundingBoxPosition.x+poi.boundingBoxSize.x*.5f,0,poi.boundingBoxPosition.z+poi.boundingBoxSize.z*.5f);
            foreach(var player in world.GetPlayers()) {
                if(player==null || player.IsDead() || player.Progression==null)continue;
                float dx=player.position.x-center.x,dz=player.position.z-center.z;
                if(dx*dx+dz*dz<=120*120)level=Math.Max(level,player.Progression.Level);
            }
            return level>0?ForestRules.ReplacementAtLevel(rule.Kind,level,ordinal):ForestRules.Replacement(rule.Kind,stage,ordinal);
        }
    }

    [HarmonyPatch(typeof(SleeperVolume),"Spawn")]
    public static class ForestSleepers
    {
        public static void Prefix(SleeperVolume __instance,World __0,ref int __1,BlockSleeper __3,int ___numSpawned,int ___gameStage)
        {
            if(__0==null || __0.IsRemote()) return;
            string name=ModApi.Replacement(__instance,___gameStage,___numSpawned,__1);
            if(name==null)return;
            int id=EntityClass.FromString(name);EntityClass definition;
            if(!EntityClass.list.TryGetValue(id,out definition))return;
            // Never break a native sleeper marker's supported animation/pose.
            if(__3!=null && __3.ExcludesWalkType(EntityAlive.GetSpawnWalkType(definition)))return;
            __1=id;
        }
    }

    [HarmonyPatch(typeof(EntityAlive),"OnAddedToWorld")]
    public static class ForestHeavySpawn
    {
        private static void Postfix(EntityAlive __instance)
        {
            if(!GameManager.IsDedicatedServer && !String.IsNullOrEmpty(__instance.EntityClass.Properties.GetString("DelveTint")) && __instance.GetComponent<ForestTint>()==null)
                __instance.gameObject.AddComponent<ForestTint>();
            if(__instance.world==null || __instance.world.IsRemote())return;
            string name=EntityClass.GetEntityClassName(__instance.entityClass);
            if(name!="delveWarpedBrute" && name!="delveThornbackBoar")return;
            if(__instance.GetComponent<HeavyAttackCycle>()==null)__instance.gameObject.AddComponent<HeavyAttackCycle>();
        }
    }

    public class ForestTint : MonoBehaviour
    {
        void Start()
        {
            var e=GetComponent<EntityAlive>();if(e==null)return;
            string[] parts=e.EntityClass.Properties.GetString("DelveTint").Split(',');if(parts.Length<3)return;
            var culture=System.Globalization.CultureInfo.InvariantCulture;
            Color tint=new Color(float.Parse(parts[0],culture),float.Parse(parts[1],culture),float.Parse(parts[2],culture),1);
            foreach(Renderer renderer in GetComponentsInChildren<Renderer>(true)) {
                Material[] materials=renderer.sharedMaterials;
                for(int i=0;i<materials.Length;i++) {
                    var material=materials[i];if(material==null)continue;
                    var block=new MaterialPropertyBlock();renderer.GetPropertyBlock(block,i);
                    foreach(string key in new[]{"_Color","_BaseColor"})if(material.HasProperty(key)) {
                        Color original=material.GetColor(key);Color result=Color.Lerp(original,tint,.55f);result.a=original.a;block.SetColor(key,result);
                    }
                    renderer.SetPropertyBlock(block,i);
                }
            }
        }
    }

    public class HeavyAttackCycle : MonoBehaviour
    {
        EntityAlive enemy;float next;int phase;
        static readonly string[] Buffs={"delveForestBrace","delveForestRush","delveForestSpent"};
        void Awake(){enemy=GetComponent<EntityAlive>();next=Time.time+8;}
        void Update()
        {
            if(enemy==null || enemy.world==null || enemy.world.IsRemote() || enemy.IsDead())return;
            if(Time.time<next)return;
            EntityAlive target=enemy.GetAttackTarget();
            if(phase==0 && (target==null || target.IsDead() || (target.position-enemy.position).sqrMagnitude>100)) {next=Time.time+1;return;}
            foreach(string buff in Buffs)enemy.Buffs.RemoveBuff(buff);
            if(phase==0) {
                enemy.Buffs.AddBuff(Buffs[0]);next=Time.time+2;phase=1;
                string sound=enemy.EntityClass.Properties.GetString("SoundAlert");
                if(!String.IsNullOrEmpty(sound))enemy.PlayOneShot(sound);
            }
            else if(phase==1){enemy.Buffs.AddBuff(Buffs[1]);next=Time.time+4;phase=2;}
            else if(phase==2){enemy.Buffs.AddBuff(Buffs[2]);next=Time.time+5;phase=3;}
            else{next=Time.time+9;phase=0;}
        }
    }

    // The original campaign counts every delve-prefixed entity as corrupted.
    // Magical wildlife is not part of that military kill objective.
    [HarmonyPatch]
    public static class WildlifeCampaignCredit
    {
        static System.Reflection.MethodBase TargetMethod(){return AccessTools.Method(AccessTools.TypeByName("Delve.Core"),"Killed");}
        static bool Prefix(ref ModEvents.SEntityKilledData __0)
        {
            if(__0.KilledEntitiy==null)return true;
            string name=EntityClass.GetEntityClassName(__0.KilledEntitiy.entityClass);
            return name!="delveThornbackBoar" && name!="delveGloomcat" && name!="delveCrystalStag";
        }
    }
}

public class ConsoleCmdForest : ConsoleCmdAbstract
{
    public override string[] getCommands(){return new[]{"forest"};}
    public override string getDescription(){return "Forest bestiary: roster | spawn <entityName> [playerId] | encounter <corrupted|room|imp|soldier> [playerId]";}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        if(args.Count==0 || args[0]=="roster"){SdtdConsole.Instance.Output(String.Join(", ",DelveForest.ModApi.Roster));return;}
        World w=GameManager.Instance.World;
        if(w==null || w.IsRemote()){SdtdConsole.Instance.Output("Run on the host in a loaded world.");return;}
        if(args.Count<2){SdtdConsole.Instance.Output(getDescription());return;}
        string[] names=args[0]=="encounter"?DelveForest.ForestRules.Encounter(args[1]):args[0]=="spawn" && Array.IndexOf(DelveForest.ModApi.Roster,args[1])>=0?new[]{args[1]}:null;
        if(names==null){SdtdConsole.Instance.Output(getDescription());return;}
        EntityPlayer player=null;int id;
        if(args.Count>2 && int.TryParse(args[2],out id))player=w.GetEntity(id) as EntityPlayer;
        else if(sender.RemoteClientInfo!=null)player=w.GetEntity(sender.RemoteClientInfo.entityId) as EntityPlayer;
        else player=w.GetPrimaryPlayer();
        if(player==null || player.IsDead() || w.IsWithinTraderArea(new Vector3i(player.position))){SdtdConsole.Instance.Output("A living player outside an NPC settlement is required.");return;}
        int count=0;
        foreach(string name in names) {
            int x,y,z;
            if(!w.FindRandomSpawnPointNearPlayer(player,20,out x,out y,out z,40) || w.IsWithinTraderArea(new Vector3i(x,y,z)))continue;
            var e=EntityFactory.CreateEntity(EntityClass.FromString(name),new Vector3(x,y,z)) as EntityAlive;
            if(e==null)continue;w.SpawnEntityInWorld(e);
            // Neutral prey must keep its native flee behavior.
            if(name!="delveCrystalStag")e.SetAttackTarget(player,120);
            count++;
        }
        SdtdConsole.Instance.Output("Spawned "+count+"/"+names.Length+" creatures at native safe positions.");
    }
}
