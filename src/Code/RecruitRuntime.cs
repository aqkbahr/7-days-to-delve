using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Xml.Serialization;
using HarmonyLib;
using UnityEngine;

namespace Delve
{
    [Serializable] public class RecruitView
    {
        public string Message="", Settlement="", Selected="";
        public List<SettlementRecord> Settlements=new List<SettlementRecord>();
        public List<RecruitRecord> Recruits=new List<RecruitRecord>();
        public bool AtShrine;
        public ulong WorldTime;
    }
    public static class Recruitment
    {
        static readonly Dictionary<string,int> bodies=new Dictionary<string,int>();
        static readonly Dictionary<int,float> requests=new Dictionary<int,float>();
        public static World World { get { return GameManager.Instance.World; } }
        static RecruitRoster Roster { get { return Core.Progress.Roster; } }
        public static void Reset() { bodies.Clear(); requests.Clear(); }
        static Vector3i Claim(SettlementRecord s) { return new Vector3i(s.X,s.Y,s.Z); }
        static Vector3i Station(RecruitRecord r) { return new Vector3i(r.X,r.Y,r.Z); }
        static PersistentPlayerData Data(EntityPlayer p) { return GameManager.Instance.persistentPlayers.GetPlayerDataFromEntityID(p.entityId); }
        static PersistentPlayerData Owner(SettlementRecord s)
        { return GameManager.Instance.persistentPlayers.Players.Values.FirstOrDefault(p=>p.PrimaryId.CombinedString==s.Owner); }
        static bool Allowed(EntityPlayer p, PersistentPlayerData owner)
        {
            var user=Data(p);
            return user!=null && owner!=null && (user.PrimaryId.Equals(owner.PrimaryId) ||
                (owner.IsAlly(user) && p.Party!=null && p.Party.ContainsMember(owner.EntityId)));
        }
        static bool Allowed(EntityPlayer p, SettlementRecord s) { return s!=null && Allowed(p,Owner(s)); }
        static bool Loaded(Vector3i pos) { return World.GetChunkSync(pos.x>>4,pos.z>>4)!=null; }
        static bool Active(SettlementRecord s)
        {
            var owner=Owner(s); var pos=Claim(s);
            if(owner==null || !owner.GetLandProtectionBlocks().Contains(pos) || !World.IsLandProtectionValidForPlayer(owner))return false;
            if(!Loaded(pos))return true;
            var claim=World.GetTileEntity(pos).GetSelfOrFeature<TEFeatureLandClaim>();
            return claim!=null && claim.IsPrimary();
        }
        static bool Contains(SettlementRecord s,Vector3i pos)
        { int radius=(GameStats.GetInt(EnumGameStats.LandClaimSize)-1)/2;return Math.Abs(pos.x-s.X)<=radius && Math.Abs(pos.z-s.Z)<=radius; }
        static bool Near(EntityPlayer p,Vector3i pos) { return Vector3.Distance(p.position,pos.ToVector3())<=6; }
        static bool Steward(EntityPlayer p,int id)
        {
            var e=World.GetEntity(id) as EntityTrader;
            return e!=null && EntityClass.GetEntityClassName(e.entityClass)=="delveWayrestSteward" && Vector3.Distance(p.position,e.position)<=6 && e.TraderData.TraderInfo.IsTraderActivitiesOpen;
        }
        static bool IsLedger(Vector3i pos) { return Loaded(pos) && World.GetBlock(pos).Block.GetBlockName()=="delveRecruitLedger"; }
        static bool IsShrine(Vector3i pos) { return Loaded(pos) && World.GetBlock(pos).Block.GetBlockName()=="delveRecoveryShrine"; }
        static SettlementRecord Register(EntityPlayer p,Vector3i ledger)
        {
            if(!Near(p,ledger) || !IsLedger(ledger))throw new InvalidOperationException("Stand beside your Settlement Ledger.");
            foreach(var owner in GameManager.Instance.persistentPlayers.Players.Values)
            {
                if(!Allowed(p,owner))continue;
                foreach(var pos in owner.GetLandProtectionBlocks())
                {
                    var probe=new SettlementRecord {Owner=owner.PrimaryId.CombinedString,X=pos.x,Y=pos.y,Z=pos.z};
                    if(!Contains(probe,ledger) || !Active(probe))continue;
                    var s=Roster.Settlements.Find(x=>x.Owner==probe.Owner && x.X==pos.x && x.Y==pos.y && x.Z==pos.z);
                    if(s==null){s=probe;s.Id=Guid.NewGuid().ToString("N");Roster.Settlements.Add(s);}
                    s.LedgerX=ledger.x;s.LedgerY=ledger.y;s.LedgerZ=ledger.z;Core.Save();return s;
                }
            }
            throw new InvalidOperationException("Place this ledger inside an active Settlement Stone owned by you or an allied member of your current party.");
        }
        public static void Handle(EntityPlayer p,string op,string sid,string rid,Vector3i pos,int npc,string receipt,int death=-1)
        {
            if(!Core.IsServer || Core.Progress==null || p==null || p.IsDead())return;
            string message="";
            try
            {
                bool atSteward=Steward(p,npc);
                bool local=Near(p,pos) && Loaded(pos);
                if(!atSteward && !local)throw new InvalidOperationException("Move closer to the Steward, ledger, recruit or station.");
                if(op!="view")
                {
                    float last;
                    if(requests.TryGetValue(p.entityId,out last) && Time.realtimeSinceStartup-last<.5f)throw new InvalidOperationException("Please wait for your previous order.");
                    requests[p.entityId]=Time.realtimeSinceStartup;
                }
                if(local && IsLedger(pos) && op=="view")sid=Register(p,pos).Id;
                if(local && IsShrine(pos) && op=="view")
                {
                    var home=Roster.Settlements.Find(x=>Allowed(p,x) && Active(x) && Contains(x,pos));
                    if(home!=null)sid=home.Id;
                    else message="Place the shrine inside a registered active Settlement Stone. Register it with a Settlement Ledger first.";
                }
                var s=Roster.Settlements.Find(x=>x.Id==sid);
                if(op=="view" && npc>=0)
                {
                    var talking=FindBody(npc);
                    if(talking!=null && Allowed(p,Roster.Settlements.Find(x=>x.Id==talking.SettlementId)))rid=talking.Id;
                }
                if(op!="view" && !Allowed(p,s))throw new InvalidOperationException("You no longer have access to that settlement.");
                var r=Roster.Recruits.Find(x=>x.Id==rid);
                if(op=="hireSmith" || op=="hireCook" || op=="hireDefender")
                {
                    if(!atSteward && !(local && IsLedger(pos)))throw new InvalidOperationException("Hire through the Steward or your Settlement Ledger.");
                    if(!Active(s))throw new InvalidOperationException("Restore an active Settlement Stone before hiring.");
                    var ledger=new Vector3i(s.LedgerX,s.LedgerY,s.LedgerZ);
                    if(!IsLedger(ledger))throw new InvalidOperationException("Visit your settlement: its treasury ledger must be loaded to hire.");
                    var tile=World.GetTileEntity(ledger);
                    if(LockManager.Instance.IsLockedServer(tile,0))throw new InvalidOperationException("Close the treasury container before hiring.");
                    var storage=tile.GetSelfOrFeature<TEFeatureStorage>();
                    string role=op.Substring(4);int cost=RecruitRoster.Price(role);
                    var gold=ItemClass.GetItem("casinoCoin",false);
                    if(storage==null || storage.CountItem(gold.ItemClass)<cost)throw new InvalidOperationException("Deposit "+cost+" gold in the settlement ledger, close its storage, then hire.");
                    if(Roster.Receipts.Contains(receipt))throw new InvalidOperationException("This hiring order has already been completed.");
                    // Server-only, serialized transaction; native storage updates synchronize to viewers.
                    int removed=storage.RemoveItems(gold,cost);
                    if(removed!=cost){if(removed>0)storage.AddItem(new ItemStack(gold,removed));throw new InvalidOperationException("Treasury changed; no recruit hired.");}
                    RecruitRecord hired=null;
                    try { hired=Roster.Hire(s.Id,role,receipt);Core.Save(); }
                    catch { if(hired!=null){Roster.Recruits.Remove(hired);Roster.Receipts.Remove(receipt);}storage.AddItem(new ItemStack(gold,cost));throw; }
                    message=hired.Name+" joins your settlement. Select the recruit, then use Manage recruits at a compatible station to assign them.";
                }
                else if(op=="resurrect")
                {
                    var source=r==null?null:Roster.Settlements.Find(x=>x.Id==r.SettlementId);
                    if(!Allowed(p,source))throw new InvalidOperationException("You cannot recover this recruit.");
                    if(!local || !IsShrine(pos) || !Active(s) || !Contains(s,pos) || World.IsWithinTraderArea(pos))throw new InvalidOperationException("Begin the ritual beside a Shrine of Return inside the selected active settlement.");
                    if(source.Owner!=s.Owner)throw new InvalidOperationException("Use a shrine belonging to the same Stone owner as this fallen recruit. Recovery does not transfer ownership.");
                    var before=r.Copy();int index=Roster.Recruits.IndexOf(r);bool began=false;
                    try { Roster.BeginRecovery(r,s.Id,pos.x,pos.y,pos.z,World.GetWorldTime(),receipt,death);began=true;Core.Save(); }
                    catch { if(began){Roster.Recruits[index]=before;Roster.Receipts.Remove(receipt);}throw; }
                    message=r.Name+" is being called home. The ritual takes one in-game hour, without a priest or payment. Their identity and tier will be preserved.";
                }
                else if(op=="assign" || op=="recall")
                {
                    if(r==null || !Allowed(p,Roster.Settlements.Find(x=>x.Id==r.SettlementId)))throw new InvalidOperationException("You cannot command this recruit.");
                    if(r.Status=="Fallen" || r.Status=="Recovering")throw new InvalidOperationException("Recover this recruit at a Shrine of Return before assigning or recalling them.");
                    if(op=="assign")
                    {
                        if(!local || !Active(s) || !Contains(s,pos) || World.IsWithinTraderArea(pos))throw new InvalidOperationException("Choose a station inside this active player settlement.");
                        string block=World.GetBlock(pos).Block.GetBlockName();
                        if(block!="delveRallyFlag" && !(World.GetTileEntity(pos) is TileEntityWorkstation))throw new InvalidOperationException("Choose a working forge, hearth, campfire or rally flag.");
                        Roster.Assign(r,s.Id,pos.x,pos.y,pos.z,block);message=r.Name+" assigned. One recruit may occupy each station.";
                    }
                    else { r.Status="Reserve";r.Station=null;message=r.Name+" returns to the settlement roster. Health is preserved."; }
                    Despawn(r);Core.Save();
                }
                else if(op!="view")throw new InvalidOperationException("Unknown recruitment order.");
            }
            catch(Exception ex){message=ex.Message;Log.Out("[Delve recruits] "+message);}
            var view=new RecruitView {Message=message,Settlement=sid,Selected=rid,AtShrine=Near(p,pos) && IsShrine(pos),WorldTime=World.GetWorldTime()};
            view.Settlements=Roster.Settlements.Where(s=>Allowed(p,s)).ToList();
            view.Recruits=Roster.Recruits.Where(r=>view.Settlements.Exists(s=>s.Id==r.SettlementId)).ToList();
            string xml;using(var writer=new StringWriter()){new XmlSerializer(typeof(RecruitView)).Serialize(writer,view);xml=writer.ToString();}
            if(p is EntityPlayerLocal)RecruitScreen.Receive(xml);
            else ConnectionManager.Instance.SendPackage(NetPackageManager.GetPackage<NetPackageDelveRecruitReply>().Setup(xml),false,p.entityId);
        }
        static void Despawn(RecruitRecord r)
        {
            int id;if(!bodies.TryGetValue(r.Id,out id))return;
            var e=World.GetEntity(id) as EntityAlive;
            if(e!=null){r.Health=Math.Max(0,Math.Min(RecruitRoster.MaxHealth(r.Role),e.Health));World.RemoveEntity(id,EnumRemoveEntityReason.Despawned);}
            bodies.Remove(r.Id);
        }
        public static RecruitRecord FindBody(int id) { var pair=bodies.FirstOrDefault(x=>x.Value==id);return pair.Key==null?null:Roster.Recruits.Find(r=>r.Id==pair.Key); }
        public static void Killed(int id)
        {
            var r=FindBody(id);if(r==null)return;
            Roster.MarkFallen(r);bodies.Remove(r.Id);Core.Save();
        }
        static void Recover(RecruitRecord r)
        {
            var home=Roster.Settlements.Find(s=>s.Id==r.RecoverySettlementId);
            var source=Roster.Settlements.Find(s=>s.Id==r.SettlementId);
            var shrine=new Vector3i(r.ShrineX,r.ShrineY,r.ShrineZ);
            var before=r.Copy();bool changed=false;
            // An unloaded shrine is unknown, not destroyed. Validate it before completion.
            if(home==null || source==null || source.Owner!=home.Owner || !Active(home) || !Contains(home,shrine) || Loaded(shrine) && !IsShrine(shrine))
            {Roster.InterruptRecovery(r);changed=true;}
            else if(Loaded(shrine))changed=Roster.CompleteRecovery(r,World.GetWorldTime());
            if(!changed)return;
            try {Core.Save();}
            catch {Roster.Recruits[Roster.Recruits.IndexOf(r)]=before;throw;}
        }
        public static void Tick()
        {
            if(!Core.IsServer || Core.Progress==null)return;
            bool changed=false;
            foreach(var r in new List<RecruitRecord>(Roster.Recruits))
            {
                if(r.Status=="Recovering"){Recover(r);continue;}
                if(r.Status!="Assigned")continue;
                int id;EntityAlive body=bodies.TryGetValue(r.Id,out id)?World.GetEntity(id) as EntityAlive:null;
                if(body!=null && body.IsDead()){Roster.MarkFallen(r);Despawn(r);changed=true;continue;}
                var s=Roster.Settlements.Find(x=>x.Id==r.SettlementId);var pos=Station(r);
                if(!Active(s) || Loaded(pos) && World.GetBlock(pos).Block.GetBlockName()!=r.Station)
                {r.Status="Displaced";r.Station=null;Despawn(r);changed=true;continue;}
                if(!Loaded(pos)) {Despawn(r);continue;}
                if(body==null)
                {
                    // Find a clear standing spot adjacent to the station, never inside a solid block.
                    Vector3 spawn=Vector3.zero;bool found=false;
                    foreach(var offset in new[]{new Vector3i(1,0,0),new Vector3i(-1,0,0),new Vector3i(0,0,1),new Vector3i(0,0,-1)})
                    {
                        var at=pos+offset;
                        if(World.GetBlock(at).isair && World.GetBlock(at+new Vector3i(0,1,0)).isair && !World.GetBlock(at+new Vector3i(0,-1,0)).isair)
                        {spawn=at.ToVector3()+new Vector3(.5f,0,.5f);found=true;break;}
                    }
                    if(!found)continue;
                    body=EntityFactory.CreateEntity(EntityClass.FromString(r.Role=="Defender"?"delveRecruitDefender":"delveRecruitWorker"),spawn) as EntityAlive;
                    if(body==null)continue;
                    body.SetEntityName(r.Name);body.Health=r.Health;World.SpawnEntityInWorld(body);bodies[r.Id]=body.entityId;
                }
                int health=Math.Max(0,Math.Min(RecruitRoster.MaxHealth(r.Role),body.Health));
                if(health!=r.Health){r.Health=health;changed=true;}
                if(Vector3.Distance(body.position,pos.ToVector3())>8)
                {
                    // Recreate at the same checked standing offsets used above;
                    // a newly obstructed post must never teleport a guard into a wall.
                    body.SetAttackTarget(null,0);Despawn(r);continue;
                }
                if(r.Station=="delveRallyFlag")
                {
                    var target=World.GetEntitiesInBounds(body,new Bounds(pos.ToVector3(),new Vector3(12,8,12))).OfType<EntityAlive>()
                        .Where(e=>(e is EntityZombie || e is EntityEnemyAnimal) && !e.IsDead() && Vector3.Distance(e.position,pos.ToVector3())<=6).OrderBy(e=>(e.position-body.position).sqrMagnitude).FirstOrDefault();
                    body.SetAttackTarget(target,100);
                    if(target!=null && target.GetAttackTarget()==null)target.SetAttackTarget(body,100);
                }
                else body.SetAttackTarget(null,0);
            }
            if(changed)Core.Save();
        }
        public static bool Staffed(Vector3i pos)
        { return Core.Progress!=null && Roster.Recruits.Exists(r=>r.Status=="Assigned" && r.Station!="delveRallyFlag" && r.X==pos.x && r.Y==pos.y && r.Z==pos.z && bodies.ContainsKey(r.Id)); }
    }
    public class EntityDelveRecruit : EntityNPC
    {
        public override bool IsSavedToFile(){return false;} // World roster is the single authority; do not duplicate bodies on load.
        public override void InitLocalActivationCommands(Action<EntityActivationCommand> add)
        {add(new EntityActivationCommand("delveRecruitTalk","ui_game_symbol_talk","Talk / manage recruit",null));}
        public override void OnEntityActivated(EntityActivationCommand command,EntityPlayerLocal p)
        {RecruitScreen.Open(p,GetBlockPosition(),entityId);}
        public override string GetActivationText(){return "Talk / manage recruit";}
    }
    public class DialogActionDelveRecruits : BaseDialogAction
    {
        public override void PerformAction(EntityPlayer p)
        {
            var local=p as EntityPlayerLocal;if(local==null)return;
            // Native trader actions use the active UI respondent. Parsed/cloned
            // custom actions are not guaranteed to have OwnerDialog assigned.
            var ui=LocalPlayerUI.GetUIForPlayer(local);
            var dialog=ui==null||ui.xui==null?null:ui.xui.Dialog;
            var npc=dialog==null?null:dialog.Respondent;
            if(npc==null || EntityClass.GetEntityClassName(npc.entityClass)!="delveWayrestSteward")return;
            RecruitScreen.Open(local,npc.GetBlockPosition(),npc.entityId);
        }
        public override BaseDialogAction Clone(){var c=new DialogActionDelveRecruits();CopyValues(c);return c;}
    }
    [HarmonyPatch(typeof(TileEntityWorkstation),"HandleRecipeQueue")]
    public static class RecruitWorkBonus
    {static void Prefix(TileEntityWorkstation __instance,ref float __0){if(Core.IsServer && Recruitment.Staffed(__instance.ToWorldPos()))__0*=1.15f;}}
    // Native enemy melee task lists predate recruit NPCs. Permit them to fight
    // a recruit when targeted, without adding traders or neutral NPCs as prey.
    [HarmonyPatch(typeof(EAIApproachAndAttackTarget),"SetData")]
    public static class RecruitEnemyMelee
    {
        static void Postfix(Dictionary<string,string> __0,List<EAIApproachAndAttackTarget.TargetClass> ___targetClasses)
        {
            string classes;
            if(___targetClasses!=null && __0.TryGetValue("class",out classes) && (classes.Contains("EntityPlayer") || classes.Contains("EntityBandit")))
                ___targetClasses.Add(new EAIApproachAndAttackTarget.TargetClass {type=typeof(EntityDelveRecruit),chaseTimeMax=0});
        }
    }
}

public class NetPackageDelveRecruitRequest : NetPackage
{
    int player,npc,x,y,z,death;string op,sid,rid,receipt;
    public NetPackageDelveRecruitRequest Setup(int p,string action,string s,string r,Vector3i pos,int n,string token,int life=-1)
    {player=p;op=action;sid=s??"";rid=r??"";x=pos.x;y=pos.y;z=pos.z;npc=n;receipt=token;death=life;return this;}
    public override NetPackageDirection PackageDirection {get{return NetPackageDirection.ToServer;}}
    public override void write(PooledBinaryWriter w){base.write(w);w.Write(player);w.Write(npc);w.Write(x);w.Write(y);w.Write(z);w.Write(op);w.Write(sid);w.Write(rid);w.Write(receipt);w.Write(death);}
    public override void read(PooledBinaryReader r){player=r.ReadInt32();npc=r.ReadInt32();x=r.ReadInt32();y=r.ReadInt32();z=r.ReadInt32();op=r.ReadString();sid=r.ReadString();rid=r.ReadString();receipt=r.ReadString();death=r.ReadInt32();}
    public override void ProcessPackage(World world,GameManager manager)
    {if(!world.IsRemote() && ValidEntityIdForSender(player,true) && op.Length<32 && sid.Length<=32 && rid.Length<=32 && receipt.Length==32)Delve.Recruitment.Handle(world.GetEntity(player) as EntityPlayer,op,sid,rid,new Vector3i(x,y,z),npc,receipt,death);}
}
public class NetPackageDelveRecruitReply : NetPackage
{
    string xml;
    public NetPackageDelveRecruitReply Setup(string s){xml=s;return this;}
    public override NetPackageDirection PackageDirection {get{return NetPackageDirection.ToClient;}}
    public override void write(PooledBinaryWriter w){base.write(w);w.Write(xml);}
    public override void read(PooledBinaryReader r){xml=r.ReadString();}
    public override void ProcessPackage(World world,GameManager manager){if(world.IsRemote() && xml.Length<262144)Delve.RecruitScreen.Receive(xml);}
}
