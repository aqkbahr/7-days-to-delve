using System;
using System.Collections.Generic;
using UnityEngine;

public class ConsoleCmdArborVerify : ConsoleCmdAbstract
{
    static ChunkManager.ChunkObserver observer;
    public override string[] getCommands(){return new[]{"arborverify"};}
    public override string getDescription(){return "Development Arbor registry, trader quest and generated prefab checks.";}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        EntityPlayer player=null;
        try {
            var w=GameManager.Instance.World;
            if(args[0]=="registry") {
                int total=0;int[] expected={0,141,100,34,5};
                for(int tier=1;tier<=4;tier++) {
                    int count=0;var pois=QuestEventManager.Current.GetPrefabsByDifficultyTier(tier);
                    foreach(var poi in pois) {
                        if(!poi.name.StartsWith("delve_arbor_"))continue;
                        if(w.GetBiomeInWorld(poi.boundingBoxPosition.x,poi.boundingBoxPosition.z).m_sBiomeName!="burnt_forest")throw new Exception("Arbor placement outside biome");
                        if(!poi.prefab.SleeperVolumeList.AnyUsedEntry)throw new Exception("No encounter volumes: "+poi.name);
                        count++;
                    }
                    if(count!=expected[tier])throw new Exception("Tier "+tier+" registered "+count+" expected "+expected[tier]);
                    total+=count;SdtdConsole.Instance.Output("[Arbor] Tier "+tier+" registered="+count);
                }
                SdtdConsole.Instance.Output("[Arbor] PASS registry: "+total+" native quest sites in burnt_forest.");return;
            }
            if(args[0]=="jobs") {
                EntityTrader trader=null;
                foreach(var entity in w.EntityAlives)if(entity is EntityTrader && Vector3.Distance(entity.position,new Vector3(-513,76,-1423))<100)trader=entity as EntityTrader;
                if(trader==null)throw new Exception("Load Arbor Camp first");
                trader.OnUpdateLive();if(trader.traderArea==null)throw new Exception("Trader area not bound");
                player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),trader.position) as EntityPlayer;player.world=w;
                player.Buffs.SetCustomVar("IntroComplete",1,false);
                var types=new HashSet<string>();var locations=new HashSet<string>();var tiers=new HashSet<int>();int offers=0;
                for(int attempt=0;attempt<30;attempt++)foreach(Quest q in trader.PopulateActiveQuests(player,4,100)) {
                    if(q.ID.Contains("buried")||q.ID.Contains("nexttrader")||q.ID.StartsWith("intro"))continue;
                    var pos=q.GetLocation();
                    if(w.GetBiomeInWorld((int)pos.x,(int)pos.z).m_sBiomeName!="burnt_forest")throw new Exception("Quest biome leak "+q.ID+" "+pos);
                    if(q.ID.Contains("restore_power"))throw new Exception("Electrical quest offered on converted site");
                    types.Add(q.ID);locations.Add(pos.ToString());tiers.Add(q.QuestClass.DifficultyTier);offers++;
                }
                if(tiers.Count!=4||locations.Count<20||types.Count<6)throw new Exception("Insufficient board variety");
                SdtdConsole.Instance.Output("[Arbor] PASS native trader: "+offers+" POI offers, "+types.Count+" quest IDs, "+locations.Count+" sites, all four tiers, same-biome selection. Types="+string.Join(",",new List<string>(types).ToArray()));return;
            }
            string name=args[1];int x=int.Parse(args[2]),ground=int.Parse(args[3]),z=int.Parse(args[4]);
            Prefab p=new Prefab();if(!p.Load(name,true,true,false,false))throw new Exception("Missing "+name);
            if(args[0]=="load") {
                if(observer!=null)GameManager.Instance.RemoveChunkObserver(observer);
                observer=GameManager.Instance.AddChunkObserver(new Vector3(x+p.size.x/2,ground,z+p.size.z/2),false,3,2);
                SdtdConsole.Instance.Output("[Arbor] Requested chunks for "+name);return;
            }
            int tested=0;
            for(int y=1;y<p.size.y-1;y++)for(int zz=1;zz<p.size.z-1;zz++)for(int xx=1;xx<p.size.x-1;xx++) {
                var b=p.GetBlock(xx,y,zz);string n=b.Block.GetBlockName();
                if(b.isair||b.ischild||!n.Contains("Shapes:")||(xx+zz+y)%31!=0)continue;
                int wx=x+xx,wy=ground+p.yOffset+y,wz=z+zz;
                if(w.GetChunkSync(wx>>4,wz>>4)==null)throw new Exception("Chunks not ready");
                var actual=w.GetBlock(wx,wy,wz);
                if(actual.type!=b.type)throw new Exception("Generated block differs "+name+" "+wx+","+wy+","+wz+" expected="+n+" actual="+actual.Block.GetBlockName());
                if(w.GetTextureFullArray(wx,wy,wz)!=p.GetTexture(xx,y,zz))throw new Exception("Paint differs");
                tested++;if(tested==24)goto done;
            }
            done:
            if(tested<3)throw new Exception("Too few sampled structure cells");
            SdtdConsole.Instance.Output("[Arbor] PASS generated "+name+": "+tested+" structural blocks and paint values.");
        }catch(Exception ex){SdtdConsole.Instance.Output("[Arbor] FAIL "+ex);}
        finally{if(player!=null)UnityEngine.Object.Destroy(player.gameObject);}
    }
}
