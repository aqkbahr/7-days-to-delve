using System;
using System.IO;
using System.Xml.Serialization;

namespace Delve
{
    [Serializable]
    public class WorldProgress
    {
        public int Schema = 1;
        public int CorruptedKills;
        public bool WardenDefeated;
        public int LastAttemptDay = -1;
        public int LastScoutingDay = -1;
        public System.Collections.Generic.List<string> WayrestReceipts = new System.Collections.Generic.List<string>();
        public bool ArborReached;
        public int WayrestCompletedDay = -1;
        public bool WayrestRefurbished;

        public bool CreditWayrest(string receipt, int day)
        {
            if (String.IsNullOrEmpty(receipt) || WayrestReceipts.Count >= 10 || WayrestReceipts.Contains(receipt)) return false;
            WayrestReceipts.Add(receipt);
            if (WayrestReceipts.Count == 10) WayrestCompletedDay = day;
            return true;
        }
    }

    public class UnsupportedStateVersionException : Exception
    {
        public UnsupportedStateVersionException() : base("Unsupported Delve save version. Use the matching mod release.") { }
    }

    // Independent of Unity: the same production save code is exercised by the
    // filesystem test harness. Never silently reset existing world progress.
    public sealed class WorldStateStore
    {
        private readonly string path;
        public bool RecoveredBackup { get; private set; }
        public WorldStateStore(string path) { this.path = path; }

        private static WorldProgress Read(string filename)
        {
            WorldProgress state;
            using (var stream = File.OpenRead(filename))
                state = (WorldProgress)new XmlSerializer(typeof(WorldProgress)).Deserialize(stream);
            if (state == null) throw new InvalidDataException("Empty Delve save.");
            if (state.Schema != 1) throw new UnsupportedStateVersionException();
            if (state.CorruptedKills < 0) throw new InvalidDataException("Invalid kill count.");
            ValidateWayrest(state);
            return state;
        }

        private static void ValidateWayrest(WorldProgress state)
        {
            if (state.WayrestReceipts == null || state.WayrestReceipts.Count > 10 ||
                new System.Collections.Generic.HashSet<string>(state.WayrestReceipts).Count != state.WayrestReceipts.Count ||
                state.WayrestReceipts.Exists(String.IsNullOrEmpty) ||
                ((state.ArborReached || state.WayrestRefurbished) && state.WayrestReceipts.Count != 10))
                throw new InvalidDataException("Invalid Wayrest campaign state.");
        }

        public WorldProgress Load()
        {
            RecoveredBackup = false;
            if (!File.Exists(path))
            {
                if (!File.Exists(path + ".bak")) return new WorldProgress();
                RecoveredBackup = true;
                return Read(path + ".bak");
            }
            try { return Read(path); }
            catch (UnsupportedStateVersionException) { throw; }
            catch
            {
                if (!File.Exists(path + ".bak")) throw;
                RecoveredBackup = true;
                return Read(path + ".bak");
            }
        }

        public void Save(WorldProgress state)
        {
            if (state == null || state.Schema != 1 || state.CorruptedKills < 0)
                throw new InvalidDataException("Refusing invalid Delve save.");
            ValidateWayrest(state);
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            string temp = path + ".tmp";
            using (var stream = new FileStream(temp, FileMode.Create, FileAccess.Write, FileShare.None))
            {
                new XmlSerializer(typeof(WorldProgress)).Serialize(stream,state);
                stream.Flush(true);
            }
            if (File.Exists(path))
            {
                string backup = RecoveredBackup ? path + ".corrupt-" + Guid.NewGuid().ToString("N") : path + ".bak";
                File.Replace(temp,path,backup);
            }
            else File.Move(temp,path);
            RecoveredBackup = false;
        }
    }
}
