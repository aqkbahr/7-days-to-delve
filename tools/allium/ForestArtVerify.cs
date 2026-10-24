using System;
using System.Collections.Generic;

public class ConsoleCmdForestVerify : ConsoleCmdAbstract
{
    public override string[] getCommands(){return new[]{"forestverify"};}
    public override string getDescription(){return "Check loaded Wayrest art and conservative doorway connectivity.";}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        try {
            Prefab p=new Prefab();
            if(!p.Load("delve_wayrest_forest",true,true,false,false))throw new Exception("Missing Forest Wayrest");
            var seen=new HashSet<int>();var todo=new Queue<int>();
            int start=30+5*60;seen.Add(start);todo.Enqueue(start);
            int[] dx={1,-1,0,0},dz={0,0,1,-1};
            while(todo.Count>0) {
                int v=todo.Dequeue(),x=v%60,z=v/60;
                for(int i=0;i<4;i++) {
                    int nx=x+dx[i],nz=z+dz[i],key=nx+nz*60;
                    if(nx<0||nz<0||nx>=60||nz>=60||seen.Contains(key))continue;
                    if(p.GetBlock(nx,2,nz).isair&&p.GetBlock(nx,3,nz).isair&&!p.GetBlock(nx,1,nz).isair){seen.Add(key);todo.Enqueue(key);}
                }
            }
            int[,] targets={{29,49},{12,30},{48,30},{13,10},{48,11}};
            for(int i=0;i<5;i++)if(!seen.Contains(targets[i,0]+targets[i,1]*60))throw new Exception("Blocked hub approach "+i);
            var w=GameManager.Instance.World;
            int[,] samples={{10,2,12},{10,3,12},{45,2,33},{7,2,29},{7,7,29}};
            foreach(int i in new[]{0,1,2,3,4}) {
                int x=samples[i,0],y=samples[i,1],z=samples[i,2];
                var actual=w.GetBlock(x-2711,y+63,z-2182);
                if(actual.type!=p.GetBlock(x,y,z).type)throw new Exception("World art block mismatch "+i);
                if(w.GetTextureFullArray(x-2711,y+63,z-2182)!=p.GetTexture(x,y,z))throw new Exception("World paint mismatch "+i);
            }
            SdtdConsole.Instance.Output("[ForestArt] PASS five hub approaches connected; native table, candle, barrel, stone wall and shingle roof match generated world blocks and paint.");
        }catch(Exception ex){SdtdConsole.Instance.Output("[ForestArt] FAIL "+ex);}
    }
}
