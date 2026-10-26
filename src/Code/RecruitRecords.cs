using System;
using System.Collections.Generic;
using System.IO;

namespace Delve
{
    [Serializable] public class SettlementRecord
    {
        public string Id, Owner;
        public int X, Y, Z, LedgerX, LedgerY, LedgerZ;
    }
    [Serializable] public class RecruitRecord
    {
        public string Id, SettlementId, Name, Role;
        public int Tier = 1, Health = 120;
        public string Status = "Reserve";
        public int X, Y, Z;
        public string Station;
        public int Deaths;
        public string RecoverySettlementId, RecoveryReceipt;
        public int ShrineX, ShrineY, ShrineZ;
        public ulong RecoveryReadyAt;
        public RecruitRecord Copy() { return (RecruitRecord)MemberwiseClone(); }
    }
    [Serializable] public class RecruitRoster
    {
        public List<SettlementRecord> Settlements = new List<SettlementRecord>();
        public List<RecruitRecord> Recruits = new List<RecruitRecord>();
        public List<string> Receipts = new List<string>();
        public static int Price(string role) { return role == "Smith" ? 400 : role == "Cook" ? 250 : role == "Defender" ? 500 : 0; }
        public static int MaxHealth(string role) { return role == "Defender" ? 240 : 120; }
        public const ulong RecoveryDuration = 1000; // Native world ticks: one in-game hour.
        public void MarkFallen(RecruitRecord r)
        {
            if(r==null || !Recruits.Contains(r) || r.Status=="Fallen" || r.Status=="Recovering")return;
            r.Deaths=checked(r.Deaths+1);r.Status="Fallen";r.Health=0;r.Station=null;
            r.X=r.Y=r.Z=0;ClearRecovery(r);
        }
        static void ClearRecovery(RecruitRecord r)
        {r.RecoverySettlementId=null;r.RecoveryReceipt=null;r.RecoveryReadyAt=0;r.ShrineX=r.ShrineY=r.ShrineZ=0;}
        public void BeginRecovery(RecruitRecord r,string settlement,int x,int y,int z,ulong now,string receipt,int death)
        {
            if(r==null || !Recruits.Contains(r) || r.Status!="Fallen")throw new InvalidOperationException("Select a fallen recruit who is not already recovering.");
            if(r.Deaths!=death)throw new InvalidOperationException("This fallen record changed. Refresh the roster before starting a ritual.");
            if(!Settlements.Exists(s=>s.Id==settlement))throw new InvalidOperationException("Choose a registered settlement for the shrine.");
            if(String.IsNullOrEmpty(receipt) || Receipts.Contains(receipt))throw new InvalidOperationException("This recovery request was already handled.");
            if(Recruits.Exists(o=>o.Status=="Recovering" && o.ShrineX==x && o.ShrineY==y && o.ShrineZ==z))throw new InvalidOperationException("This shrine is already tending another recruit.");
            ulong due=checked(now+RecoveryDuration);
            r.Status="Recovering";r.Health=0;r.Station=null;r.X=r.Y=r.Z=0;
            r.RecoverySettlementId=settlement;r.RecoveryReceipt=receipt;r.ShrineX=x;r.ShrineY=y;r.ShrineZ=z;r.RecoveryReadyAt=due;
            Receipts.Add(receipt);
        }
        public bool CompleteRecovery(RecruitRecord r,ulong now)
        {
            if(r==null || !Recruits.Contains(r) || r.Status!="Recovering" || now<r.RecoveryReadyAt)return false;
            // Restore the existing record, never manufacture a replacement hire.
            r.SettlementId=r.RecoverySettlementId;r.Status="Reserve";r.Health=MaxHealth(r.Role);r.Station=null;
            r.X=r.Y=r.Z=0;ClearRecovery(r);return true;
        }
        public void InterruptRecovery(RecruitRecord r)
        {
            if(r==null || !Recruits.Contains(r) || r.Status!="Recovering")return;
            r.Status="Fallen";r.Health=0;ClearRecovery(r); // Source settlement and identity never moved.
        }
        public static bool Compatible(string role, string station)
        {
            if (station == "delveRallyFlag") return Price(role) > 0;
            return role == "Smith" && (station == "delveForgeAnvil" || station == "forge") ||
                   role == "Cook" && (station == "delveFieldHearth" || station == "campfire");
        }
        public RecruitRecord Hire(string settlement, string role, string receipt)
        {
            if (Price(role) == 0 || !Settlements.Exists(s => s.Id == settlement)) throw new InvalidOperationException("Choose a valid settlement and role.");
            if (String.IsNullOrEmpty(receipt) || Receipts.Contains(receipt)) throw new InvalidOperationException("This hiring request was already handled.");
            if (Recruits.Count >= 512) throw new InvalidOperationException("This world has reached its recruit limit.");
            var r = new RecruitRecord { Id=Guid.NewGuid().ToString("N"), SettlementId=settlement, Role=role,
                Name=role+" "+(Recruits.Count+1), Health=MaxHealth(role) };
            Recruits.Add(r); Receipts.Add(receipt); return r;
        }
        public void Assign(RecruitRecord r, string settlement, int x, int y, int z, string station)
        {
            if (r == null || !Recruits.Contains(r) || r.Status == "Fallen" || r.Status == "Recovering" || !Settlements.Exists(s => s.Id == settlement)) throw new InvalidOperationException("Recruit is unavailable.");
            if (!Compatible(r.Role, station)) throw new InvalidOperationException("Smiths need a forge; cooks need a hearth or campfire. Any recruit can guard a rally flag.");
            if (Recruits.Exists(o => o != r && o.Status == "Assigned" && o.X == x && o.Y == y && o.Z == z)) throw new InvalidOperationException("Another recruit already occupies that station.");
            r.SettlementId=settlement; r.X=x; r.Y=y; r.Z=z; r.Station=station; r.Status="Assigned";
        }
        public void Validate()
        {
            if (Settlements == null || Recruits == null || Receipts == null || Recruits.Count > 512) throw new InvalidDataException("Invalid recruit roster.");
            var settlements=new HashSet<string>(); var claims=new HashSet<string>(); var ids=new HashSet<string>(); var stations=new HashSet<string>();var shrines=new HashSet<string>();
            foreach(var s in Settlements)
                if (String.IsNullOrEmpty(s.Id) || String.IsNullOrEmpty(s.Owner) || !settlements.Add(s.Id) || !claims.Add(s.Owner+":"+s.X+":"+s.Y+":"+s.Z)) throw new InvalidDataException("Invalid settlement identity.");
            foreach(var r in Recruits)
            {
                if (String.IsNullOrEmpty(r.Id) || !ids.Add(r.Id) || !settlements.Contains(r.SettlementId) || Price(r.Role)==0 || r.Tier<1 || r.Tier>6 || r.Health<0 || r.Health>MaxHealth(r.Role) || r.Deaths<0 || String.IsNullOrEmpty(r.Name)) throw new InvalidDataException("Invalid recruit identity.");
                if (r.Status!="Assigned" && r.Status!="Reserve" && r.Status!="Displaced" && r.Status!="Fallen" && r.Status!="Recovering") throw new InvalidDataException("Invalid recruit status.");
                if (r.Status=="Assigned" && (!Compatible(r.Role,r.Station) || !stations.Add(r.X+":"+r.Y+":"+r.Z))) throw new InvalidDataException("Invalid or duplicate station assignment.");
                if(r.Status=="Recovering")
                {
                    if(r.Health!=0 || r.Station!=null || r.RecoveryReadyAt==0 || !settlements.Contains(r.RecoverySettlementId) || String.IsNullOrEmpty(r.RecoveryReceipt) || !Receipts.Contains(r.RecoveryReceipt) || !shrines.Add(r.ShrineX+":"+r.ShrineY+":"+r.ShrineZ))throw new InvalidDataException("Invalid shrine recovery.");
                }
                else if(r.RecoveryReadyAt!=0 || r.RecoverySettlementId!=null || r.RecoveryReceipt!=null)throw new InvalidDataException("Stale shrine recovery.");
            }
            if (new HashSet<string>(Receipts).Count!=Receipts.Count || Receipts.Exists(String.IsNullOrEmpty)) throw new InvalidDataException("Invalid recruitment receipts.");
        }
    }
}

