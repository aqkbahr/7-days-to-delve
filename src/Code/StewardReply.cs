using HarmonyLib;
namespace Delve
{
    // The native v3 dialogue window contains choices only; custom lore has no voice track.
    public class XUiC_StewardReply : XUiController
    {
        string previous;
        string Reply {
            get {
                if(xui==null || xui.Dialog==null)return "";
                var group=xui.Dialog.DialogWindowGroup;
                var npc=xui.Dialog.Respondent;
                if(group==null || npc==null || npc.NPCInfo==null || npc.NPCInfo.DialogID!="delveWayrest")return "";
                var dialog=group.CurrentDialog;
                return dialog==null || dialog.CurrentStatement==null?"":dialog.CurrentStatement.Text;
            }
        }
        public override void Update(float dt){base.Update(dt);var text=Reply;if(text!=previous){previous=text;RefreshBindings();}}
        public void RefreshReply(){previous=Reply;ViewComponent.IsVisible=!string.IsNullOrEmpty(previous);RefreshBindings();}
        public override bool GetBindingValueInternal(ref string value,string name){
            if(name=="delve_reply"){value=Reply;return true;}
            if(name=="delve_reply_visible"){value=string.IsNullOrEmpty(Reply)?"false":"true";return true;}
            return base.GetBindingValueInternal(ref value,name);
        }
    }
    [HarmonyPatch(typeof(XUiC_DialogWindowGroup),"OnOpen")]
    public static class StewardReplyOpen {
        static void Postfix(XUiC_DialogWindowGroup __instance){Refresh(__instance);}
        public static void Refresh(XUiC_DialogWindowGroup group){var reply=group.xui.GetWindowByType<XUiC_StewardReply>();if(reply!=null)reply.RefreshReply();}
    }
    [HarmonyPatch(typeof(XUiC_DialogWindowGroup),"RefreshDialog")]
    public static class StewardReplyChange {static void Postfix(XUiC_DialogWindowGroup __instance){StewardReplyOpen.Refresh(__instance);}}
}
