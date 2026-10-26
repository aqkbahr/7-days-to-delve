using System;
using System.IO;
using System.Xml;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace DelveForest
{
    // One small server-owned record; no changes to native player save formats.
    public static class ForestCampaign
    {
        public static int FirstNight { get; private set; }
        static bool ready;
        static string path;
        static float next;
        static bool interruptedBoss;
        static readonly Type Core=AccessTools.TypeByName("Delve.Core");
        static readonly FieldInfo Active=AccessTools.Field(Core,"activeBoss");
        public static void Start(ref ModEvents.SGameStartDoneData data)
        {
            ready=false;FirstNight=0;interruptedBoss=false;next=0;
            var w=GameManager.Instance.World;if(w==null || w.IsRemote())return;
            path=Path.Combine(GameIO.GetSaveGameDir(),"Delve","forest.xml");
            try {
                if(File.Exists(path)) {
                    var doc=new XmlDocument();doc.Load(path);
                    FirstNight=int.Parse(doc.DocumentElement.GetAttribute("firstNight"));
                    interruptedBoss=doc.DocumentElement.GetAttribute("bossActive")=="true";
                }
                ready=true;
                if(interruptedBoss) {
                    // Core deliberately despawns orphan bosses. Allow a fresh attempt
                    // in the remaining arrival window instead of silently losing it.
                    object progress=AccessTools.Field(Core,"Progress").GetValue(null);
                    if(progress!=null && !(bool)AccessTools.Field(progress.GetType(),"WardenDefeated").GetValue(progress)) {
                        AccessTools.Field(progress.GetType(),"LastAttemptDay").SetValue(progress,-1);
                        AccessTools.Method(Core,"Save").Invoke(null,null);
                    }
                    interruptedBoss=false;
                }
                Save();
            } catch(Exception ex) {ready=false;Log.Error("[DelveForest] Campaign state unavailable; preserving file: "+ex.Message);}
        }
        public static int Night(World world)
        {
            int day=GameUtils.WorldTimeToDays(world.GetWorldTime()),hour=GameUtils.WorldTimeToHours(world.GetWorldTime());
            int dawn=GameUtils.CalcDuskDawnHours(GameStats.GetInt(EnumGameStats.DayLightLength)).Item2;
            return hour<dawn?day-1:day;
        }
        public static bool ObserveHorde(World world)
        {
            if(!ready || world==null || world.IsRemote())return false;
            int night=Night(world);
            if(FirstNight==0){FirstNight=night;Save();}
            return FirstNight==night;
        }
        public static void Update(ref ModEvents.SGameUpdateData data)
        {
            if(!ready || Time.realtimeSinceStartup<next)return;
            next=Time.realtimeSinceStartup+1;
            CaptureEncounter();
        }
        public static void CaptureEncounter()
        {
            if(!ready)return;
            bool active=(int)Active.GetValue(null)>=0;
            if(active!=interruptedBoss){interruptedBoss=active;Save();}
        }
        public static void Stop(ref ModEvents.SWorldShuttingDownData data)
        {
            // Retain the most recently observed active encounter even if Core's
            // shutdown handler already cleared its runtime ID.
            if(ready)Save();ready=false;
        }
        static void Save()
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            string temporary=path+".tmp";
            var doc=new XmlDocument();var root=doc.CreateElement("forest");doc.AppendChild(root);
            root.SetAttribute("firstNight",FirstNight.ToString());root.SetAttribute("bossActive",interruptedBoss?"true":"false");
            doc.Save(temporary);
            if(File.Exists(path))File.Replace(temporary,path,path+".bak");else File.Move(temporary,path);
        }
    }

    [HarmonyPatch]
    public static class ForestEncounterPersistence
    {
        static System.Collections.Generic.IEnumerable<MethodBase> TargetMethods()
        {
            var core=AccessTools.TypeByName("Delve.Core");
            foreach(string method in new[]{"SpawnBoss","Withdraw","CompleteBoss"})yield return AccessTools.Method(core,method);
        }
        static void Postfix(){ForestCampaign.CaptureEncounter();}
    }

    [HarmonyPatch(typeof(AIDirectorBloodMoonParty),"SpawnZombie")]
    public static class ForestHordeContext
    {
        [ThreadStatic] public static int Level;
        [ThreadStatic] public static bool First;
        [ThreadStatic] public static bool Inside;
        public struct Context { public int Level;public bool First,Inside; }
        static void Prefix(World __0,EntityPlayer __1,out Context __state)
        {
            __state=new Context{Level=Level,First=First,Inside=Inside};
            Inside=__0!=null && !__0.IsRemote() && __1!=null;
            Level=Inside && __1.Progression!=null?__1.Progression.Level:0;
            First=Inside && ForestCampaign.ObserveHorde(__0);
        }
        static Exception Finalizer(Exception __exception,Context __state)
        {
            Level=__state.Level;First=__state.First;Inside=__state.Inside;return __exception;
        }
    }

    [HarmonyPatch(typeof(EntityGroups),"GetRandomEntityFromGroupMaxTier")]
    public static class ForestHordeSelection
    {
        static void Prefix(ref string __0)
        {
            if(!ForestHordeContext.Inside)return;
            string name=ForestRules.HordeGroup(__0,ForestHordeContext.Level,ForestHordeContext.First);
            if(EntityGroups.list[name]!=null)__0=name;
        }
    }
}
