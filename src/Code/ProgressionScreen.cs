using System;
using System.Collections.Generic;
using System.Globalization;
using HarmonyLib;
namespace Delve
{
    public class XUiC_ProgressionGroup : XUiController
    {
        public override void OnOpen()
        {
            base.OnOpen();xui.playerUI.windowManager.Open("windowpaging",false);
            var group=xui.FindWindowGroupByName("windowpaging");
            var selector=group==null?null:group.GetChildByType<XUiC_WindowSelector>();
            if(selector!=null)selector.SetSelected("skills");
        }
    }
    public class XUiC_ProgressionScreen : XUiController
    {
        readonly Dictionary<string,string> bindings=new Dictionary<string,string>();
        readonly List<SkillUiDefinition> choices=new List<SkillUiDefinition>();
        int tab,attribute,node,page;bool masteries,opened;float elapsed;
        SkillUiDefinition skill;string message="";string[] pages=new string[]{""};
        EntityPlayerLocal Player {get{return xui.playerUI.entityPlayer;}}
        void Put(string key,object value) {bindings["dg_"+key]=value is bool?((bool)value?"true":"false"):Convert.ToString(value,CultureInfo.InvariantCulture);}
        void Hook(string id,Action action)
        {
            var button=GetChildById(id) as XUiC_SimpleButton;
            if(button==null)throw new InvalidOperationException("Missing Delve UI button: "+id);
            button.OnPressed+=(sender,mouse)=>{if(mouse==-1){action();Refresh();}};
        }
        public override void Init()
        {
            base.Init();
            Hook("dg_close",()=>xui.playerUI.windowManager.Close("skills"));
            Hook("dg_knowledge",()=>{xui.playerUI.windowManager.Close("skills");xui.playerUI.windowManager.Open("delveKnowledge",true);});
            for(int i=0;i<5;i++){int index=i;Hook("dg_tab"+i,()=>SelectTab(index));}
            for(int i=0;i<9;i++){int index=i;Hook("dg_skill"+i,()=>{if(index<choices.Count){skill=choices[index];node=page=0;masteries=false;message="";}});}
            for(int i=0;i<6;i++){int index=i;Hook("dg_attribute"+i,()=>{attribute=index;page=0;message="";});Hook("dg_mastery"+i,()=>{node=14+index;page=0;message="";});}
            for(int i=0;i<14;i++){int index=i;Hook("dg_node"+i,()=>{node=index;page=0;message="";});}
            Hook("dg_toggleMastery",()=>{if(skill==null || skill.Perks.Length<=14)return;masteries=!masteries;node=masteries?14:0;page=0;});
            Hook("dg_descPrev",()=>page=Math.Max(0,page-1));Hook("dg_descNext",()=>page=Math.Min(pages.Length-1,page+1));
            Hook("dg_purchase",Buy);SelectTab(0);
        }
        void SelectTab(int value)
        {
            tab=value;choices.Clear();foreach(var s in ProgressionUiData.Skills)if(s.Tab==tab)choices.Add(s);
            if(tab==1)choices.Add(SummoningUi.Skill());
            skill=choices.Count>0?choices[0]:null;node=page=0;masteries=false;message="";
        }
        public override void OnOpen(){base.OnOpen();opened=true;CharacterProgression.Initialize(Player);Refresh();}
        public override void OnClose(){opened=false;base.OnClose();}
        public override void Update(float dt){base.Update(dt);if(opened && (elapsed+=dt)>=.5f){elapsed=0;Refresh();}}
        public override bool GetBindingValueInternal(ref string value,string name)
        {
            // XUi chooses and caches the binding owner while constructing views,
            // before OnOpen has a player. Claim our namespace even before values exist.
            if(name.StartsWith("dg_",StringComparison.Ordinal))
            {if(!bindings.TryGetValue(name,out value))value=InitialBinding(name);return true;}
            return base.GetBindingValueInternal(ref value,name);
        }
        static string InitialBinding(string name)
        {
            if(name=="dg_progressfill")return "0";
            if(name=="dg_hasmasteries" || name.StartsWith("dg_nodevisible") || name=="dg_attributes" || name=="dg_skills" || name=="dg_ordinary" || name=="dg_masteries" || name=="dg_canpurchase" || name=="dg_descriptionpaging" || name.StartsWith("dg_skillvisible") || name.StartsWith("dg_masteryvisible") || name.StartsWith("dg_tabselected"))return "false";
            if(name.StartsWith("dg_nodecolor"))return "185,185,185";
            return "";
        }
        bool Owned(PerkUiDefinition perk){return ProgressionRuntime.Owns(Player,perk.Id);}
        bool CanBuy(PerkUiDefinition perk)
        {
            var v=Player.Progression.GetProgressionValue(perk.Id);
            return v!=null && !Owned(perk) && ProgressionRuntime.Eligible(Player,perk.Id) && v.CanPurchase(Player,v.Level+1) && Player.Progression.SkillPoints>=v.CostForNextLevel;
        }
        string State(PerkUiDefinition perk)
        {
            var def=TalentCatalog.Entries[perk.Id];
            if(Owned(perk))return def.Implemented?"Owned":"Owned / effect pending";
            if(!def.Implemented)return "In development";
            if(CanBuy(perk))return "Available";
            if(ProgressionRuntime.Eligible(Player,perk.Id))return "Needs a skill point";
            return "Locked";
        }
        string Card(PerkUiDefinition perk)
        {return perk.Name+"\n"+State(perk).Replace("Needs a skill point","No points").Replace("Owned / effect pending","Owned (pending)")+"  /  Rank "+TalentCatalog.Entries[perk.Id].Rank;}
        void Refresh()
        {
            if(Player==null || Player.Progression==null)return;
            CharacterProgression.ReconcileTalents(Player);
            Put("budget","Level "+Player.Progression.Level+" / 80     Skill points: "+Player.Progression.SkillPoints+"     Attribute points: "+CharacterProgression.UnspentAttributes(Player));
            Put("attributes",tab==0);Put("skills",tab!=0);Put("ordinary",!masteries);Put("masteries",masteries);
            string[] tabs={"ATTRIBUTES","COMBAT","ARMOR","MOVEMENT","CRAFTING"};Put("listtitle",tabs[tab]);
            for(int i=0;i<5;i++)Put("tabselected"+i,tab==i);
            for(int i=0;i<9;i++)
            {
                Put("skillvisible"+i,i<choices.Count);
                Put("skilltext"+i,i<choices.Count?(skill==choices[i]?"> ":"")+choices[i].Title+"\nRank "+ProficiencyRules.Rank(CharacterProgression.Get(Player,"delvePractice"+choices[i].Id))+" / 100":"");
            }
            Put("sidehint",tab==0?"One attribute point per level gained.\nFive more from the tutorial.":"Practice raises rank.\nSkill points buy perks.\nTree cap: 15 points.");
            if(tab==0)AttributeDetails();else if(skill!=null)SkillDetails();
            Put("descriptionpaging",pages.Length>1);page=Math.Max(0,Math.Min(page,pages.Length-1));Put("description",pages[page]);
            Put("descriptionpage",pages.Length>1?(page+1)+" / "+pages.Length:"");Put("message",message);
            RefreshBindingsSelfAndChildren();
        }
        void AttributeDetails()
        {
            for(int i=0;i<6;i++)
            {
                string n=CharacterProgression.Attributes[i];var v=Player.Progression.GetProgressionValue("delveAtt"+n);
                Put("attributetext"+i,(attribute==i?"> ":"")+n+"\n"+(v==null?1:v.Level)+" / 20");
            }
            string name=CharacterProgression.Attributes[attribute];var value=Player.Progression.GetProgressionValue("delveAtt"+name);
            int level=value==null?1:value.Level;bool available=value!=null && level<20 && CharacterProgression.UnspentAttributes(Player)>0;
            Put("detailtitle",name);Put("detailstatus","Base rank "+level+" / 20");
            pages=ProgressionUiModel.Pages(Localization.Get("delveAtt"+name+"Desc"),30,10);
            Put("requirements",level>=20?"Attribute cap reached.":"Next rank: "+(level+1)+"\nCost: 1 attribute point\nAvailable: "+CharacterProgression.UnspentAttributes(Player));
            Put("canpurchase",available);Put("purchasecaption",level>=20?"At maximum":"Raise "+name);
        }
        void SkillDetails()
        {
            float practice=ProficiencyRules.Credit(CharacterProgression.Get(Player,"delvePractice"+skill.Id),0);int rank=ProficiencyRules.Rank(practice);
            Put("title",skill.Title+"  /  Proficiency "+rank+" of 100");
            Put("progress",rank==100?"Maximum proficiency reached":((int)practice-ProficiencyRules.Threshold(rank))+" / "+ProficiencyRules.NextCost(rank)+" practice toward rank "+(rank+1));
            Put("progressfill",ProgressionUiModel.Fraction(practice));Put("training",skill.Training);
            Put("hasmasteries",skill.Perks.Length>14);
            for(int i=0;i<3;i++)Put("branch"+i,skill.Branches[i]);
            for(int i=0;i<14;i++)
            {
                var perk=skill.Perks[i];Put("nodevisible"+i,perk!=null);if(perk==null){Put("nodetext"+i,"");continue;}Put("nodetext"+i,(node==i?"> ":"")+Card(perk));
                Put("nodecolor"+i,Owned(perk)?"136,215,174":!TalentCatalog.Entries[perk.Id].Implemented?"146,170,190":CanBuy(perk)?"240,211,139":"185,185,185");
            }
            for(int i=0;i<6;i++){Put("masteryvisible"+i,14+i<skill.Perks.Length);Put("masterytext"+i,14+i<skill.Perks.Length?Card(skill.Perks[14+i]):"");}
            Put("masterytoggle",masteries?"Back to branches":"View mastery choices");
            node=Math.Min(node,skill.Perks.Length-1);if(skill.Perks[node]==null)node=0;var selected=skill.Perks[node];var def=TalentCatalog.Entries[selected.Id];
            Put("detailtitle",selected.Name);Put("detailstatus",State(selected));pages=ProgressionUiModel.Pages(selected.Description,30,10);
            int owned=0;foreach(string key in def.Prerequisites)if(ProgressionRuntime.Owns(Player,key))owned++;
            string req="Proficiency: "+rank+" / "+def.Rank+"\nPrerequisites: "+owned+" / "+def.Prerequisites.Length;
            if(def.Rank==100)req+="\nOne mastery; trial pending.";else req+="\nCost: 1 skill point";
            Put("requirements",req);Put("canpurchase",CanBuy(selected));Put("purchasecaption",Owned(selected)?"Already owned":!def.Implemented?"In development":"Learn perk (1 point)");
        }
        void Buy()
        {
            CharacterProgression.Initialize(Player);
            if(tab==0)
            {
                var v=Player.Progression.GetProgressionValue("delveAtt"+CharacterProgression.Attributes[attribute]);
                message=v!=null && CharacterProgression.BuyAttribute(Player,v,v.Level+1)?"Attribute increased.":"No attribute point available, or cap reached.";return;
            }
            if(skill==null || node>=skill.Perks.Length || skill.Perks[node]==null)return;
            var perk=skill.Perks[node];if(!CanBuy(perk)){message="Requirements are not met. No points spent.";return;}
            var value=Player.Progression.GetProgressionValue(perk.Id);int cost=value.CostForNextLevel;
            value.Level++;Player.Progression.SkillPoints-=cost;
            Player.MinEventContext.ProgressionValue=value;Player.FireEvent(MinEventTypes.onPerkLevelChanged,true);
            xui.Recipes.RefreshTrackedRecipe();
            if(!ConnectionManager.Instance.IsServer)ConnectionManager.Instance.SendToServer(NetPackageManager.GetPackage<NetPackageEntitySetSkillLevelServer>().Setup(Player.entityId,value.Name,value.Level),false);
            QuestEventManager.Current.SpendSkillPoint(value);Player.bPlayerStatsChanged=true;message="Learned "+perk.Name+".";
        }
    }
    [HarmonyPatch(typeof(XUiC_SkillWindowGroup),"Init")]
    public static class KnowledgeReturnButton
    {
        static void Postfix(XUiC_SkillWindowGroup __instance)
        {
            var button=__instance.GetChildById("dg_backToProgression") as XUiC_SimpleButton;
            if(button!=null)button.OnPressed+=(sender,mouse)=>{if(mouse==-1){__instance.xui.playerUI.windowManager.Close("delveKnowledge");__instance.xui.playerUI.windowManager.Open("skills",true);}};
        }
    }
    [HarmonyPatch(typeof(XUiC_CharacterFrameWindow),"Init")]
    public static class CharacterProgressionButton
    {
        static void Postfix(XUiC_CharacterFrameWindow __instance)
        {
            var button=__instance.GetChildById("dg_characterProgression") as XUiC_SimpleButton;
            if(button!=null)button.OnPressed+=(sender,mouse)=>{if(mouse==-1){__instance.xui.playerUI.windowManager.Close("character");__instance.xui.playerUI.windowManager.Open("skills",true);}};
        }
    }
}

