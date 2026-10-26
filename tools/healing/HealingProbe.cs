using System;
using System.Collections.Generic;
using Delve;
using HarmonyLib;
using UnityEngine;

// Isolated synthetic fixture; never included in a player package.
public class ConsoleCmdHealingProbe : ConsoleCmdAbstract
{
    public override string[] getCommands(){return new[]{"healingprobe"};}
    public override string getDescription(){return "Validate healing on an unspawned fixture.";}
    static void Check(bool ok,string name){if(!ok)throw new Exception(name);}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        EntityAlive target=null;
        try
        {
            var patches=Harmony.GetPatchInfo(AccessTools.Method(typeof(ItemActionRanged),"fireShot"));
            Check(patches!=null && patches.Prefixes.Count>0,"healing cast patch absent");
            target=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),Vector3.zero) as EntityAlive;
            Check(target!=null,"fixture creation");
            target.world=GameManager.Instance.World;
            int max=target.GetMaxHealth();
            target.Health=max-30;
            Check(HealingTotem.Apply(target,20)==20 && target.Health==max-10,"actual engine healing");
            Check(HealingTotem.Apply(target,20)==10 && target.Health==max,"engine overheal clamp");
            Check(HealingTotem.Apply(target,20)==0,"no full health credit");
            target.SetDead();
            Check(HealingTotem.Apply(target,20)==0,"no resurrection");
            SdtdConsole.Instance.Output("HEALING PASS: cast patch, actual health restoration, overheal, full-health credit, dead target. Synthetic fixture; client casting remains untested.");
        }
        catch(Exception ex){SdtdConsole.Instance.Output("HEALING FAIL: "+ex);}
        finally{if(target!=null)UnityEngine.Object.Destroy(target.gameObject);}
    }
}
