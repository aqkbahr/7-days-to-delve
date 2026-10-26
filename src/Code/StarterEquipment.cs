using System;
using System.IO;

namespace Delve
{
    // Read-only checks against the actual loaded engine data, used by delve verify.
    public static class StarterEquipment
    {
        static void Require(bool condition, string message)
        { if(!condition) throw new InvalidDataException("Starter equipment: "+message); }
        public static int Verify()
        {
            int checks=0;
            string[] tools={"Wand","Staff","Totem"};
            int[] damages={18,42,10};
            int[] capacities={8,1,4};
            for(int i=0;i<tools.Length;i++)
            {
                string name="delveStarter"+tools[i], rune="delve"+tools[i]+"Rune";
                ItemValue weapon=ItemClass.GetItem(name,false), ammo=ItemClass.GetItem(rune,false);
                Require(weapon.ItemClass.Actions[0] is ItemActionRanged,name+" has no ranged action"); checks++;
                Require(Math.Abs(EffectManager.GetValue(PassiveEffects.MagazineSize,weapon)-capacities[i])<.01f,name+" capacity"); checks++;
                Require(Math.Abs(EffectManager.GetValue(PassiveEffects.EntityDamage,ammo)-damages[i])<.01f,rune+" damage"); checks++;
                Require(TrainingHooks.CraftedSkill(name,"")=="Carpentry",name+" craft skill"); checks++;
                Require(TrainingHooks.CraftedSkill(rune,"")=="Alchemy",rune+" craft skill"); checks++;
            }
            string[] categories={"Light","Medium","Heavy"};
            ItemValue mending=ItemClass.GetItem("delveMendingTotem",false), healingRune=ItemClass.GetItem("delveHealingRune",false);
            Require(mending.ItemClass.Actions[0] is ItemActionRanged,"Mending Totem ranged/reload action"); checks++;
            Require(EffectManager.GetValue(PassiveEffects.MagazineSize,mending)==4,"Mending capacity"); checks++;
            Require(EffectManager.GetValue(PassiveEffects.EntityDamage,healingRune)==0,"Healing rune must not damage entities"); checks++;
            Require(EffectManager.GetValue(PassiveEffects.BlockDamage,healingRune)==0,"Healing rune must not damage terrain"); checks++;
            Require(TrainingHooks.CraftedSkill("delveMendingTotem","")=="Carpentry","Mending crafting"); checks++;
            Require(TrainingHooks.CraftedSkill("delveHealingRune","")=="Alchemy","Healing rune crafting"); checks++;
            for(int i=0;i<categories.Length;i++)
                foreach(string slot in new[]{"Helmet","Outfit","Gloves","Boots"})
                {
                    string name="armorDelve"+categories[i]+slot;
                    ItemValue item=ItemClass.GetItem(name,false);
                    Require(Math.Abs(EffectManager.GetValue(PassiveEffects.PhysicalDamageResist,item)-(6+3*i))<.01f,name+" protection"); checks++;
                    Require(TrainingHooks.CraftedSkill(name,"")==(i==2 ? "Smithing" : "Carpentry"),name+" craft skill"); checks++;
                }
            return checks;
        }
    }
}
