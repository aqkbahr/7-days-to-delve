using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using Delve;
public class ConsoleCmdRecruitProbe : ConsoleCmdAbstract
{
    static ChunkManager.ChunkObserver observer;
    public override string[] getCommands(){return new[]{"recruitprobe"};}
    public override string getDescription(){return "Isolated recruitment definition and native object verification";}
    static void Check(bool c,string text){if(!c)throw new Exception(text);SdtdConsole.Instance.Output("[Recruits] PASS "+text);}
    public override void Execute(List<string> args,CommandSenderInfo sender)
    {
        var made=new List<Entity>();
        try
        {
            var world=GameManager.Instance.World;if(world==null || Core.Progress==null)throw new Exception("Wait for world startup");
            if(args.Count>0 && args[0]=="load") {observer=GameManager.Instance.AddChunkObserver(new Vector3(0,80,0),false,3,2);SdtdConsole.Instance.Output("[Recruits] Loading isolated fixture terrain");return;}
            if(args.Count>0 && args[0]=="flow") {Flow(world);return;}
            if(args.Count>0 && args[0]=="resurrection") {Flow(world,true);return;}
            foreach(string role in new[]{"Worker","Defender"})
            {
                var entity=EntityFactory.CreateEntity(EntityClass.FromString("delveRecruit"+role),new Vector3(0,100,0)) as EntityDelveRecruit;
                Check(entity!=null,"custom "+role+" entity class resolves");made.Add(entity);
                Check(entity.GetMaxHealth()==(role=="Worker"?120:240),role+" health = "+entity.GetMaxHealth());
                Check(!entity.IsSavedToFile(),"roster is sole persistent authority for "+role);
                var hand=ItemClass.GetItem("meleeHandDelve"+role,false);
                float damage=EffectManager.GetValue(PassiveEffects.EntityDamage,hand,0,entity);
                Check(Math.Abs(damage-(role=="Worker"?8:20))<.01f,role+" melee damage = "+damage);
                var commands=new List<EntityActivationCommand>();entity.InitLocalActivationCommands(commands.Add);
                Check(commands.Count==1 && commands[0].commandId=="delveRecruitTalk","recruit interaction registered");
            }
            Check(Block.GetBlockValue("delveRecruitLedger",false).Block is BlockDelveRecruitLedger,"ledger block class");
            Check(Block.GetBlockValue("delveRallyFlag",false).Block is BlockDelveRallyFlag,"rally flag block class");
            Check(Block.GetBlockValue("delveRecoveryShrine",false).Block is BlockDelveRecoveryShrine,"resurrection shrine block class");
            var player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),new Vector3(0,100,0)) as EntityPlayer;made.Add(player);player.world=world;
            foreach(string item in new[]{"delveRecruitLedger","delveRallyFlag","delveRecoveryShrine"})
            {var recipe=CraftingManager.GetRecipe(item);Check(recipe!=null && RecipeProgression.Allowed(recipe,player),item+" recipe allowed by Forest gate");}
            Check(Dialog.DialogList["delveWayrest"].GetResponse("wayrestOpenRoster")!=null,"Steward roster response loaded");
            Check(Dialog.DialogList["delveWayrest"].GetResponse("wayrestResurrection")!=null,"Steward resurrection explanation loaded");
            Check(ReflectionHelpers.GetTypeWithPrefix("DialogAction","Delve.DialogActionDelveRecruits, Delve")==typeof(DialogActionDelveRecruits),"custom dialogue action resolves");
            Check(ReflectionHelpers.GetTypeWithPrefix("XUiC_","Delve.XUiC_RecruitScreen, Delve")==typeof(XUiC_RecruitScreen),"roster UI controller resolves");
            Check(NetPackageManager.GetPackageId(typeof(NetPackageDelveRecruitRequest))>=0,"request network package registered");
            Check(NetPackageManager.GetPackageId(typeof(NetPackageDelveRecruitReply))>=0,"reply network package registered");
            var guard=made.OfType<EntityDelveRecruit>().Last();guard.world=world;
            var enemy=EntityFactory.CreateEntity(EntityClass.FromString("delveCorruptedWalker"),new Vector3(2,100,0)) as EntityAlive;made.Add(enemy);enemy.world=world;
            guard.SetAttackTarget(enemy,100);enemy.SetAttackTarget(guard,100);
            var guardAI=new EAIApproachAndAttackTarget();guardAI.Init(guard);guardAI.SetData(new Dictionary<string,string>{{"class","EntityZombie,0,EntityEnemyAnimal,0"}});
            var enemyAI=new EAIApproachAndAttackTarget();enemyAI.Init(enemy);enemyAI.SetData(new Dictionary<string,string>{{"class","EntityPlayer,0,EntityBandit,0"}});
            Check(guardAI.CanExecute() && enemyAI.CanExecute(),"native guard and enemy melee tasks accept each other");
            int hp=guard.Health;var source=new DamageSourceEntity(EnumDamageSource.External,EnumDamageTypes.Slashing,enemy.entityId);source.SetIgnoreConsecutiveDamages(true);guard.DamageEntity(source,20,false,0);
            Check(guard.Health<hp,"recruit is vulnerable to enemy damage");
            SdtdConsole.Instance.Output("[Recruits] PASS native recruitment definitions and object construction. Human UI/combat and multiplayer acceptance still required.");
        }
        catch(Exception ex){SdtdConsole.Instance.Output("[Recruits] FAIL "+ex);}
        finally{foreach(var e in made)if(e!=null)UnityEngine.Object.Destroy(e.gameObject);}
    }
    static void Order(EntityPlayer p,string op,string sid,string rid,Vector3i pos,string token)
    {
        var field=typeof(Recruitment).GetField("requests",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic);
        ((Dictionary<int,float>)field.GetValue(null)).Clear();
        var record=Core.Progress.Roster.Recruits.Find(r=>r.Id==rid);
        Recruitment.Handle(p,op,sid,rid,pos,-1,token,record==null?-1:record.Deaths);
    }
    static void Flow(World w,bool resurrection=false)
    {
        if(w.GetPlayers().Count>0)throw new Exception("Fixture requires no connected players");
        if(w.GetChunkSync(0,0)==null)throw new Exception("Run recruitprobe load first");
        var original=Core.Progress;var pp=GameManager.Instance.persistentPlayers;ulong originalTime=w.GetWorldTime();
        var user=PlatformUserIdentifierAbs.FromPlatformAndId("Steam","76561198000000991",false);
        if(pp.GetPlayerData(user)!=null)throw new Exception("Fixture identity already exists");
        EntityPlayer player=null;var old=new List<BlockChangeInfo>();
        var claim=new Vector3i(2,w.GetHeightAt(2,2)+2,2);var ledger=claim+new Vector3i(2,0,0);var forge=claim+new Vector3i(4,0,0);var flag=claim+new Vector3i(0,0,3);
        var shrine=claim+new Vector3i(4,0,3);
        try
        {
            Core.Progress=new WorldProgress();Recruitment.Reset();
            player=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),ledger.ToVector3()) as EntityPlayer;player.world=w;
            w.Entities.Add(player.entityId,player);w.Players.Add(player.entityId,player);
            var pd=pp.CreatePlayerData(user,user,"RecruitFixture",(Platform.EPlayGroup)0);pd.EntityId=player.entityId;pp.MapPlayer(pd);
            var changes=new List<BlockChangeInfo>();
            for(int x=0;x<=8;x++)for(int z=0;z<=7;z++)for(int y=claim.y-1;y<=claim.y+2;y++)
            {var p=new Vector3i(x,y,z);old.Add(new BlockChangeInfo(new BlockValueRef(p),w.GetBlock(p)));changes.Add(new BlockChangeInfo(new BlockValueRef(p),y==claim.y-1?Block.GetBlockValue("woodLogPillar100",false):BlockValue.Air));}
            w.SetBlocksRPC(changes);
            foreach(var pair in new[]{new KeyValuePair<Vector3i,string>(claim,"keystoneBlock"),new KeyValuePair<Vector3i,string>(ledger,"delveRecruitLedger"),new KeyValuePair<Vector3i,string>(forge,"delveForgeAnvil"),new KeyValuePair<Vector3i,string>(flag,"delveRallyFlag"),new KeyValuePair<Vector3i,string>(shrine,"delveRecoveryShrine")})
            {
                var block=Block.GetBlockValue(pair.Value,false);w.SetBlocksRPC(new List<BlockChangeInfo>{new BlockChangeInfo(new BlockValueRef(pair.Key),block)});
                var tile=w.GetTileEntity(pair.Key) as TileEntityComposite;if(tile!=null)tile.OnBlockAdded(pair.Key,block,user);
            }
            pp.PlaceLandProtectionBlock(claim,user);
            Order(player,"view","","",ledger,Guid.NewGuid().ToString("N"));
            Check(Core.Progress.Roster.Settlements.Count==1,"native claim registers communal ledger");
            var s=Core.Progress.Roster.Settlements[0];var storage=w.GetTileEntity(ledger).GetSelfOrFeature<TEFeatureStorage>();var coin=ItemClass.GetItem("casinoCoin",false);
            Check(storage!=null && storage.AddItem(new ItemStack(coin,1000)),"native treasury accepts gold");
            string token=Guid.NewGuid().ToString("N");Order(player,"hireSmith",s.Id,"",ledger,token);
            Check(Core.Progress.Roster.Recruits.Count==1 && storage.CountItem(coin.ItemClass)==600,"server hire charges exact cost");
            Order(player,"hireSmith",s.Id,"",ledger,token);
            Check(Core.Progress.Roster.Recruits.Count==1 && storage.CountItem(coin.ItemClass)==600,"replay neither charges nor duplicates");
            var r=Core.Progress.Roster.Recruits[0];player.SetPosition(forge.ToVector3(),false);
            Order(player,"assign",s.Id,r.Id,forge,Guid.NewGuid().ToString("N"));Recruitment.Tick();
            Check(r.Status=="Assigned" && w.EntityAlives.Any(e=>e is EntityDelveRecruit),"assigned worker materializes beside station");
            Check(Recruitment.Staffed(forge),"worker enables station crafting bonus");
            if(resurrection)
            {
                r.Name="Tamsin Reed";r.Tier=3;string id=r.Id;
                var dead=w.EntityAlives.First(e=>e is EntityDelveRecruit);dead.SetDead();Recruitment.Tick();
                Check(r.Status=="Fallen" && r.Health==0 && r.Deaths==1 && !Recruitment.Staffed(forge),"native death frees station and retains fallen record");
                Order(player,"resurrect",s.Id,id,forge,Guid.NewGuid().ToString("N"));
                Check(r.Status=="Fallen","recovery outside a shrine is rejected");
                player.SetPosition(shrine.ToVector3(),false);
                var shrineOutsider=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),shrine.ToVector3()) as EntityPlayer;shrineOutsider.world=w;
                try{Order(shrineOutsider,"resurrect",s.Id,id,shrine,Guid.NewGuid().ToString("N"));Check(r.Status=="Fallen","outsider cannot resurrect another settlement's recruit");}
                finally{UnityEngine.Object.Destroy(shrineOutsider.gameObject);}
                string ritual=Guid.NewGuid().ToString("N");Order(player,"resurrect",s.Id,id,shrine,ritual);
                Check(r.Status=="Recovering" && r.RecoveryReadyAt==w.GetWorldTime()+1000 && storage.CountItem(coin.ItemClass)==600,"priest-free ritual begins with a saved timer and no charge");
                var other=Core.Progress.Roster.Hire(s.Id,"Cook",Guid.NewGuid().ToString("N"));Core.Progress.Roster.MarkFallen(other);
                Order(player,"resurrect",s.Id,other.Id,shrine,Guid.NewGuid().ToString("N"));Check(other.Status=="Fallen","one active ritual per shrine enforced");
                Order(player,"recall",s.Id,id,shrine,Guid.NewGuid().ToString("N"));Check(r.Status=="Recovering","recall cannot bypass the ritual");
                Core.Save();Core.Progress=new WorldStateStore(System.IO.Path.Combine(GameIO.GetSaveGameDir(),"Delve","world.xml")).Load();
                r=Core.Progress.Roster.Recruits.Find(x=>x.Id==id);
                Check(r.Status=="Recovering" && r.Tier==3 && r.Name=="Tamsin Reed","native save reload preserves ritual identity and tier");
                w.worldTime=r.RecoveryReadyAt-1;Recruitment.Tick();Check(r.Status=="Recovering","runtime refuses early completion");
                w.worldTime=r.RecoveryReadyAt;Recruitment.Tick();
                Check(r.Status=="Reserve" && r.Id==id && r.Tier==3 && r.Name=="Tamsin Reed" && r.Role=="Smith" && r.Health==120 && r.Station==null,"runtime resurrection preserves identity and returns full-health reserve");
                Order(player,"resurrect",s.Id,id,shrine,ritual);Check(r.Status=="Reserve" && Core.Progress.Roster.Recruits.Count==2,"duplicate recovery does not create another person");
                Order(player,"assign",s.Id,id,forge,Guid.NewGuid().ToString("N"));Recruitment.Tick();
                Check(r.Status=="Assigned" && Recruitment.Staffed(forge) && w.EntityAlives.Count(e=>e is EntityDelveRecruit && !e.IsDead())==1,"recovered recruit can be redeployed as one living body");
                dead=w.EntityAlives.First(e=>e is EntityDelveRecruit && !e.IsDead());dead.SetDead();Recruitment.Tick();
                Order(player,"resurrect",s.Id,id,shrine,Guid.NewGuid().ToString("N"));
                w.SetBlocksRPC(new List<BlockChangeInfo>{new BlockChangeInfo(new BlockValueRef(shrine),BlockValue.Air)});Recruitment.Tick();
                Check(r.Status=="Fallen" && r.Tier==3 && r.Id==id && r.Deaths==2,"destroyed shrine interrupts without losing identity or tier");
                w.SetBlocksRPC(new List<BlockChangeInfo>{new BlockChangeInfo(new BlockValueRef(shrine),Block.GetBlockValue("delveRecoveryShrine",false))});
                Order(player,"resurrect",s.Id,id,shrine,Guid.NewGuid().ToString("N"));pp.RemoveLandProtectionBlock(claim);Recruitment.Tick();
                Check(r.Status=="Fallen" && r.Id==id && r.Tier==3,"claim loss keeps fallen record recoverable");
                SdtdConsole.Instance.Output("[Resurrection] PASS native death, shrine gating, access, timer, occupancy, save/reload, resurrection, redeployment, shrine destruction and claim loss");
                return;
            }
            var body=w.EntityAlives.First(e=>e is EntityDelveRecruit);body.Health=53;Recruitment.Tick();
            Order(player,"recall",s.Id,r.Id,forge,Guid.NewGuid().ToString("N"));
            Check(r.Status=="Reserve" && r.Health==53 && !Recruitment.Staffed(forge),"recall preserves health and removes station bonus");
            Order(player,"assign",s.Id,r.Id,flag,Guid.NewGuid().ToString("N"));Recruitment.Tick();
            Check(r.Status=="Assigned" && r.Station=="delveRallyFlag","worker can take rally duty");
            var guardBody=w.EntityAlives.First(e=>e is EntityDelveRecruit);guardBody.SetPosition(flag.ToVector3()+new Vector3(12,0,0),false);Recruitment.Tick();Recruitment.Tick();
            Check(r.Status=="Assigned" && w.EntityAlives.Any(e=>e is EntityDelveRecruit && Vector3.Distance(e.position,flag.ToVector3())<3),"guard returns to checked standing space after leash");
            var outsider=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),ledger.ToVector3()) as EntityPlayer;outsider.world=w;
            try
            {
                int balance=storage.CountItem(coin.ItemClass);
                Order(outsider,"recall",s.Id,r.Id,ledger,Guid.NewGuid().ToString("N"));
                Order(outsider,"hireDefender",s.Id,"",ledger,Guid.NewGuid().ToString("N"));
                Check(r.Status=="Assigned" && storage.CountItem(coin.ItemClass)==balance && Core.Progress.Roster.Recruits.Count==1,"unregistered outsider cannot recall or spend settlement gold");
            }
            finally {UnityEngine.Object.Destroy(outsider.gameObject);}
            pp.RemoveLandProtectionBlock(claim);Recruitment.Tick();
            Check(r.Status=="Displaced" && r.Health==53,"claim loss preserves displaced recruit");
            SdtdConsole.Instance.Output("[Recruits] PASS native hire/treasury/replay/assignment/body/recall/displacement flow");
        }
        finally
        {
            foreach(var e in new List<EntityAlive>(w.EntityAlives))if(e is EntityDelveRecruit)w.RemoveEntity(e.entityId,EnumRemoveEntityReason.Despawned);
            pp.RemoveLandProtectionBlock(claim);pp.UnmapPlayer(user);pp.Players.Remove(user);
            if(player!=null){w.Entities.Remove(player.entityId);w.Players.Remove(player.entityId);UnityEngine.Object.Destroy(player.gameObject);}
            if(old.Count>0)w.SetBlocksRPC(old);w.worldTime=originalTime;Core.Progress=original;Recruitment.Reset();Core.Save();
        }
    }
}


