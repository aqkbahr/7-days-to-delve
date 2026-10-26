using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Xml.Serialization;
using HarmonyLib;

namespace Delve
{
    public static class RecruitScreen
    {
        public static RecruitView View=new RecruitView();
        public static string Settlement="",Selected="";
        public static Vector3i Position;
        public static int NPC=-1;
        public static bool Waiting;
        public static void Open(EntityPlayerLocal p,Vector3i position,int npc=-1)
        {
            Position=position;NPC=npc;View=new RecruitView();Waiting=false;
            p.PlayerUI.windowManager.Close("dialog");
            p.PlayerUI.windowManager.Open("delveRecruits",true);
            Send(p,"view");
        }
        public static void Send(EntityPlayerLocal p,string action)
        {
            if(Waiting)return;Waiting=true;
            string receipt=Guid.NewGuid().ToString("N");
            var selected=View.Recruits.Find(r=>r.Id==Selected);int death=selected==null?-1:selected.Deaths;
            if(Core.IsServer)Recruitment.Handle(p,action,Settlement,Selected,Position,NPC,receipt,death);
            else ConnectionManager.Instance.SendToServer(NetPackageManager.GetPackage<NetPackageDelveRecruitRequest>().Setup(p.entityId,action,Settlement,Selected,Position,NPC,receipt,death),false);
        }
        public static void Receive(string xml)
        {
            using(var reader=new StringReader(xml))View=(RecruitView)new XmlSerializer(typeof(RecruitView)).Deserialize(reader);
            Waiting=false;
            if(View.Recruits.Exists(r=>r.Id==View.Selected))Selected=View.Selected;
            if(View.Settlements.Exists(s=>s.Id==View.Settlement))Settlement=View.Settlement;
            if(!View.Settlements.Exists(s=>s.Id==Settlement))Settlement=View.Settlements.Count==0?"":View.Settlements[0].Id;
        }
    }
    public class XUiC_RecruitScreen : XUiController
    {
        readonly Dictionary<string,string> bindings=new Dictionary<string,string>();int page;float elapsed,wait,poll;bool opened;
        EntityPlayerLocal Player{get{return xui.playerUI.entityPlayer;}}
        void Hook(string id,Action action){((XUiC_SimpleButton)GetChildById(id)).OnPressed+=(s,b)=>{if(b==-1){action();Refresh();}};}
        public override void Init()
        {
            base.Init();Hook("nr_close",()=>xui.playerUI.windowManager.Close("delveRecruits"));
            Hook("nr_refresh",()=>RecruitScreen.Send(Player,"view"));
            Hook("nr_settlement",()=>{var list=RecruitScreen.View.Settlements;if(list.Count>0){int i=list.FindIndex(s=>s.Id==RecruitScreen.Settlement);RecruitScreen.Settlement=list[(i+1)%list.Count].Id;page=0;}});
            Hook("nr_prev",()=>page=Math.Max(0,page-1));Hook("nr_next",()=>page++);
            for(int i=0;i<8;i++){int row=i;Hook("nr_row"+i,()=>{var list=RecruitScreen.View.Recruits;int n=page*8+row;if(n<list.Count)RecruitScreen.Selected=list[n].Id;});}
            foreach(string op in new[]{"hireSmith","hireCook","hireDefender","assign","recall","resurrect"}){string action=op;Hook("nr_"+op,()=>RecruitScreen.Send(Player,action));}
        }
        public override void OnOpen(){base.OnOpen();opened=true;page=0;wait=poll=0;Refresh();}
        public override void OnClose(){opened=false;base.OnClose();}
        public override void Update(float dt)
        {
            base.Update(dt);
            if(!opened)return;
            if(RecruitScreen.Waiting){wait+=dt;if(wait>10){RecruitScreen.Waiting=false;RecruitScreen.View.Message="No reply yet. Refresh the roster before placing another order.";wait=0;}}
            else wait=0;
            if((poll+=dt)>=5){poll=0;if(!RecruitScreen.Waiting && RecruitScreen.View.Recruits.Exists(r=>r.Status=="Recovering"))RecruitScreen.Send(Player,"view");}
            if((elapsed+=dt)>.25f){elapsed=0;Refresh();}
        }
        void Refresh()
        {
            var v=RecruitScreen.View;var s=v.Settlements.Find(x=>x.Id==RecruitScreen.Settlement);
            bindings["nr_atshrine"]=v.AtShrine?"true":"false";
            bindings["nr_settlement"]=s==null?"No settlement registered":"Stone at "+s.X+", "+s.Z+"  (click to change)";
            page=Math.Max(0,Math.Min(page,Math.Max(0,(v.Recruits.Count-1)/8)));
            bindings["nr_page"]="Roster "+(page+1)+" / "+Math.Max(1,(v.Recruits.Count+7)/8);
            for(int i=0;i<8;i++){int n=page*8+i;bindings["nr_row"+i]=n<v.Recruits.Count?(v.Recruits[n].Id==RecruitScreen.Selected?"> ":"")+v.Recruits[n].Name+" | "+v.Recruits[n].Status:"";}
            var r=v.Recruits.Find(x=>x.Id==RecruitScreen.Selected);
            bindings["nr_detail"]=r==null?"Select a recruit from the roster.\n\nAt home: hold Interact on a station and choose Manage recruits, select the recruit, then Assign here.\n\nTo transfer, select the destination Stone above. You must have access to both settlements.":
                r.Name+" | Tier "+r.Tier+" | Health "+r.Health+"/"+RecruitRoster.MaxHealth(r.Role)+"\n"+r.Status+(r.Status=="Assigned"?" at "+r.X+", "+r.Y+", "+r.Z:"")+"\n\n"+
                (r.Role=="Smith"?"\"Give me a forge and supplies, and I will keep the work moving.\"\nAssigned forge: 15% faster queued crafting.":r.Role=="Cook"?"\"A warm meal makes a hard day bearable. Show me the hearth.\"\nAssigned hearth or campfire: 15% faster queued crafting.":"\"Mark my rally point. I will hold the ground around it.\"\nGuards within 6m of a rally flag; returns if drawn beyond 8m.")+"\n\nWorkers can guard rally flags too, with less health and damage. Recall keeps the recruit and health in reserve. Fallen recruits can return through a Shrine of Return.";
            if(r!=null && (r.Status=="Fallen" || r.Status=="Recovering"))
            {
                ulong left=r.RecoveryReadyAt>v.WorldTime?r.RecoveryReadyAt-v.WorldTime:0;
                bindings["nr_detail"]=r.Name+" | "+r.Role+" | Tier "+r.Tier+"\n"+r.Status+"\n\n"+
                    (r.Status=="Fallen"?"Their record is safe. Craft a Shrine of Return (30 stone, 10 wood, 5 cloth), place it inside a registered active Stone, then interact with it and select this recruit.\n\nChoose Resurrect to begin a one-hour in-game ritual. No priest or payment is required.":
                    "The shrine is calling them home.\n"+(left>0?Math.Ceiling(left*60.0/1000).ToString("0")+" in-game minutes remain.":"Return to the shrine to finish if its area is unloaded.")+"\nShrine: "+r.ShrineX+", "+r.ShrineY+", "+r.ShrineZ+"\n\nIf the shrine or claim is lost, their fallen record remains available to try again.")+
                    "\n\nThe same person returns to reserve at full health, with identity, role and tier intact. Assign them to a station afterward.";
            }
            bindings["nr_message"]=RecruitScreen.Waiting?"Waiting for the settlement steward...":v.Message;
            RefreshBindings();
        }
        public override bool GetBindingValueInternal(ref string value,string name){if(bindings.TryGetValue(name,out value))return true;return base.GetBindingValueInternal(ref value,name);}
    }
    public class BlockDelveRecruitLedger : BlockCompositeTileEntity
    {
        public override BlockActivationCommand[] GetBlockActivationCommands(WorldBase w,BlockValue b,Vector3i pos,EntityAlive p)
        {var list=new List<BlockActivationCommand>(base.GetBlockActivationCommands(w,b,pos,p));list.Add(new BlockActivationCommand("delveRecruits","ui_game_symbol_talk",true,false,"Manage recruits"));return list.ToArray();}
        public override bool OnBlockActivated(string command,WorldBase w,Vector3i pos,BlockValue b,EntityPlayerLocal p)
        {if(command=="delveRecruits"){RecruitScreen.Open(p,pos);return true;}return base.OnBlockActivated(command,w,pos,b,p);}
    }
    public class BlockDelveRallyFlag : Block
    {
        public override bool HasBlockActivationCommands(WorldBase w,BlockValue b,Vector3i pos,EntityAlive p){return true;}
        public override BlockActivationCommand[] GetBlockActivationCommands(WorldBase w,BlockValue b,Vector3i pos,EntityAlive p)
        {return new[]{new BlockActivationCommand("delveRecruits","ui_game_symbol_talk",true,false,"Manage recruits")};}
        public override bool OnBlockActivated(WorldBase w,Vector3i pos,BlockValue b,EntityPlayerLocal p){RecruitScreen.Open(p,pos);return true;}
        public override bool OnBlockActivated(string command,WorldBase w,Vector3i pos,BlockValue b,EntityPlayerLocal p){RecruitScreen.Open(p,pos);return true;}
    }
    public class BlockDelveRecoveryShrine : Block
    {
        public override bool HasBlockActivationCommands(WorldBase w,BlockValue b,Vector3i pos,EntityAlive p){return true;}
        public override BlockActivationCommand[] GetBlockActivationCommands(WorldBase w,BlockValue b,Vector3i pos,EntityAlive p)
        {return new[]{new BlockActivationCommand("delveResurrection","ui_game_symbol_talk",true,false,"Recover fallen recruits")};}
        public override bool OnBlockActivated(WorldBase w,Vector3i pos,BlockValue b,EntityPlayerLocal p){RecruitScreen.Open(p,pos);return true;}
        public override bool OnBlockActivated(string command,WorldBase w,Vector3i pos,BlockValue b,EntityPlayerLocal p)
        {if(command!="delveResurrection")return false;RecruitScreen.Open(p,pos);return true;}
    }
    [HarmonyPatch(typeof(BlockWorkstation),"GetBlockActivationCommands")]
    public static class RecruitStationMenu
    {
        static void Postfix(BlockValue __1,ref BlockActivationCommand[] __result)
        {string name=__1.Block.GetBlockName();if(!RecruitRoster.Compatible("Smith",name) && !RecruitRoster.Compatible("Cook",name))return;var list=new List<BlockActivationCommand>(__result);list.Add(new BlockActivationCommand("delveRecruits","ui_game_symbol_talk",true,false,"Manage recruits"));__result=list.ToArray();}
    }
    [HarmonyPatch(typeof(BlockWorkstation),"OnBlockActivated",new[]{typeof(string),typeof(WorldBase),typeof(Vector3i),typeof(BlockValue),typeof(EntityPlayerLocal)})]
    public static class RecruitStationActivate
    {static bool Prefix(string __0,Vector3i __2,EntityPlayerLocal __4,ref bool __result){if(__0!="delveRecruits")return true;RecruitScreen.Open(__4,__2);__result=true;return false;}}
}

