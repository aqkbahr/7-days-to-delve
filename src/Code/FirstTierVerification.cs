using System;
using System.IO;
namespace Delve
{
    public static class FirstTierVerification
    {
        static int count;
        static void Check(bool value,string name){count++;if(!value)throw new InvalidDataException("First tier: "+name);}
        public static int Verify()
        {
            count=0;
            foreach(string skill in ProficiencyRules.Skills)
            {
                int basics=0;foreach(var pair in TalentCatalog.Entries)if(pair.Value.Skill==skill && pair.Value.Rank==10){Check(pair.Value.Implemented,"missing "+pair.Key);basics++;}
                Check(basics==2,"fundamentals count "+skill);
            }
            foreach(string name in new[]{"delveBladeWound","delveCombo","delveTotemDecay"})Check(BuffManager.GetBuff(name)!=null,"buff "+name);
            var recipe=CraftingManager.GetRecipe("delveIronDagger");var item=new ItemValue(ItemClass.GetItem("delveIronDagger",false).type,1,1,false,null,1);
            int ordinary=item.MaxUseTimes;CraftedProperties.Stamp(item,recipe,130);
            Check(item.MaxUseTimes>ordinary,"crafted metal durability applies (before="+ordinary+", after="+item.MaxUseTimes+", material="+item.ItemClass.MadeOfMaterial.id+")");
            var stream=new MemoryStream();var writer=new PooledBinaryWriter();writer.SetBaseStream(stream);
            item.Write(writer);writer.Flush();stream.Position=0;var reader=new PooledBinaryReader();reader.SetBaseStream(stream);
            var restored=new ItemValue();restored.Read(reader);Check(restored.MaxUseTimes==item.MaxUseTimes,"crafted metadata survives item serialization");
            stream=new MemoryStream();writer=new PooledBinaryWriter();writer.SetBaseStream(stream);
            var job=new RecipeQueueItem{Recipe=recipe,Multiplier=2,Quality=1,StartingEntityId=42,CraftingTimeLeft=7,OneItemCraftTime=10};
            CraftedProperties.Data.GetOrCreateValue(job).Flags=131|Rank20Crafting.Extraction;CraftedProperties.Data.GetOrCreateValue(job).YieldCarry=.45f;job.Write(writer);writer.Write(1234567);writer.Flush();
            byte[] extended=stream.ToArray();stream.Position=0;reader=new PooledBinaryReader();reader.SetBaseStream(stream);var loaded=new RecipeQueueItem();loaded.Read(reader);
            Check(CraftedProperties.Data.GetOrCreateValue(loaded).Flags==(131|Rank20Crafting.Extraction),"queued maker snapshot survives serialization");
            Check(Math.Abs(CraftedProperties.Data.GetOrCreateValue(loaded).YieldCarry-.45f)<.00001f,"fractional extraction survives serialization");
            Check(loaded.Multiplier==2 && loaded.StartingEntityId==42 && loaded.CraftingTimeLeft==7,"queue payload intact");
            Check(reader.ReadInt32()==1234567,"queue extension does not consume following data");
            // Reconstruct a native version-2 record (same payload, no extension).
            var legacy=new byte[extended.Length-8];Array.Copy(extended,legacy,extended.Length-12);Array.Copy(extended,extended.Length-4,legacy,legacy.Length-4,4);legacy[0]=2;legacy[1]=0;
            stream=new MemoryStream(legacy);reader=new PooledBinaryReader();reader.SetBaseStream(stream);loaded=new RecipeQueueItem();loaded.Read(reader);
            Check(CraftedProperties.Data.GetOrCreateValue(loaded).Flags==128,"legacy queues gain no retroactive maker bonus");
            Check(reader.ReadInt32()==1234567,"native queue compatibility");
            var previous=new byte[extended.Length-7];Array.Copy(extended,previous,extended.Length-12);previous[0]=(byte)(53505&255);previous[1]=(byte)(53505>>8);previous[previous.Length-5]=131;Array.Copy(extended,extended.Length-4,previous,previous.Length-4,4);
            stream=new MemoryStream(previous);reader=new PooledBinaryReader();reader.SetBaseStream(stream);loaded=new RecipeQueueItem();loaded.Read(reader);
            Check(CraftedProperties.Data.GetOrCreateValue(loaded).Flags==131&&CraftedProperties.Data.GetOrCreateValue(loaded).YieldCarry==0,"previous Delve queue compatibility");
            Check(reader.ReadInt32()==1234567,"previous extension boundary");
            return count;
        }
    }
}
