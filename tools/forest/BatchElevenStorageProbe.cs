using System;using System.IO;using System.Collections.Generic;using System.Reflection;using UnityEngine;using Delve;
public class ConsoleCmdBatchElevenStorageProbe:ConsoleCmdAbstract{
 public override string[] getCommands(){return new[]{"batch11storage"};}public override string getDescription(){return "Batch 4 backend storage and configuration regression tests; no UI interaction.";}
 static int checks;static void Check(bool b,string s){if(!b)throw new Exception(s);checks++;}
 static TEFeatureStorage Store(Chunk c,int x,int count,bool owned){var b=Block.GetBlockValue("cntWoodWritableCrate",false);c.SetBlockRaw(x,100,0,b);var te=new TileEntityComposite(c,b);te.localChunkPos=new Vector3i(x,100,0);c.AddTileEntity(te);var s=te.GetFeature<TEFeatureStorage>();s.ItemGrid.PlayerOwned=owned;s.ItemGrid.SetItem(0,new ItemStack(ItemClass.GetItem("resourceRockSmall",false),count));return s;}
 static void Field(object o,string n,object v){o.GetType().GetField(n,BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic).SetValue(o,v);}
 public override void Execute(List<string> args,CommandSenderInfo sender){EntityAlive p=null;try{checks=0;NearbyCrafting.Station=null;
  if(args.Count>0&&args[0]=="plants"){
   var world=GameManager.Instance.World;var found=new Dictionary<Vector3i,string>();
   for(int x=-2860;x<-2740;x++)for(int z=-2060;z<-1940;z++){
    if(world.GetChunkSync(x>>4,z>>4)==null)continue;int h=world.GetTerrainHeight(x,z);
    for(int y=h;y<=h+3;y++){string n=world.GetBlock(x,y,z).Block.GetBlockName();if(n.StartsWith("planted")&&!n.Contains("Player"))found[new Vector3i(x,y,z)]=n;}
   }int paired=0;foreach(var kv in found){bool near=false;foreach(var other in found){if(kv.Key==other.Key||kv.Value!=other.Value)continue;int dx=kv.Key.x-other.Key.x,dz=kv.Key.z-other.Key.z;if(dx*dx+dz*dz<=25){near=true;break;}}if(near)paired++;}
   Check(found.Count>=20,"wild sample contains at least twenty plants; actual="+found.Count);Check(paired*100>=found.Count*75,"same-species neighbors within five meters; "+paired+"/"+found.Count);
   SdtdConsole.Instance.Output("[Batch04Plants] PASS "+found.Count+" naturally generated wild plants; "+paired+" have same-species neighbors within 5m; no POI mutation");return;
  }
  int pressed=0;var controller=new XUiController();controller.OnPress+=(s,button)=>{Check(button==-1,"native left-click event ID");pressed++;};controller.Pressed(-1);controller.Pressed(0);controller.Pressed(-2);Check(pressed==1,"only native left click dispatches OnPress");
  Check(NearbyCrafting.InRange(5,0,0)&&NearbyCrafting.InRange(3,4,0)&&!NearbyCrafting.InRange(5,1,0)&&!NearbyCrafting.InRange(6,0,0),"3D five-meter radius boundary");
  var chunk=new Chunk(0,0);var a=Store(chunk,0,10,true);var b=Store(chunk,1,15,true);var poi=Store(chunk,2,50,false);
  var ta=chunk.GetTileEntity(new Vector3i(0,100,0)) as TileEntityComposite;var tb=chunk.GetTileEntity(new Vector3i(1,100,0)) as TileEntityComposite;var tp=chunk.GetTileEntity(new Vector3i(2,100,0)) as TileEntityComposite;
  Check(NearbyCrafting.Accessible(ta),"player storage allowed");Check(!NearbyCrafting.Accessible(tp),"POI supplies excluded");ta.SetUserAccessing(true);Check(!NearbyCrafting.Accessible(ta),"busy storage excluded");ta.SetUserAccessing(false);
  var locked=tb.GetFeature<TEFeatureLockable>();locked.SetLocked(true);Check(!NearbyCrafting.Accessible(tb),"locked unauthorized box excluded");locked.SetLocked(false);
  p=EntityFactory.CreateEntity(EntityClass.FromString("playerMale"),Vector3.zero) as EntityAlive;p.world=GameManager.Instance.World;
  var inv=new XUiM_PlayerInventory(null,null);Field(inv,"backpack",p.bag);Field(inv,"toolbelt",p.inventory);Field(inv,"currencyItem",ItemClass.GetItem("casinoCoin",false));
  var stone=ItemClass.GetItem("resourceRockSmall",false);p.bag.SetSlots(ItemStack.CreateArray(45));p.inventory.SetSlots(ItemStack.CreateArray(10));p.bag.AddItem(new ItemStack(stone,3));
  var stores=new List<TEFeatureStorage>{a,b};var requirements=new List<ItemStack>{new ItemStack(stone,5)};var removed=new List<ItemStack>();
  NearbyCrafting.ConsumeFrom(inv,stores,requirements,3,removed);Check(NearbyCrafting.InventoryCount(inv,stone)==0,"inventory consumed first");Check(a.ItemGrid[0].count==0&&b.ItemGrid[0].count==13,"three queued recipes consume fifteen total across inventory and boxes");int paid=0;foreach(var i in removed)paid+=i.count;Check(paid==15,"native refund list records exact payment");
  int before=NearbyCrafting.Count(stores,stone);bool refused=false;try{NearbyCrafting.ConsumeFrom(inv,stores,requirements,100,new List<ItemStack>());}catch(InvalidOperationException){refused=true;}Check(refused&&NearbyCrafting.Count(stores,stone)==before,"insufficient materials leave all storage unchanged");
  var duplicate=new List<ItemStack>{new ItemStack(stone,10),new ItemStack(stone,10)};refused=false;try{NearbyCrafting.ConsumeFrom(inv,stores,duplicate,1,new List<ItemStack>());}catch(InvalidOperationException){refused=true;}Check(refused&&NearbyCrafting.Count(stores,stone)==before,"duplicate ingredient totals validated before spending");
  b.ItemGrid.SetLocked(0,true);Check(NearbyCrafting.Count(stores,stone)==0,"reserved slots excluded");b.ItemGrid.SetLocked(0,false);
  int runes=0;foreach(var r in CraftingManager.GetAllRecipes()){string n=r.GetName();if(n.Contains("Rune")&&(n.Contains("Wand")||n.Contains("Staff"))){runes++;bool metal=false;foreach(var i in r.ingredients){string id=i.itemValue.ItemClass.GetItemName();Check(!id.Contains("Chrysanthemum")&&!id.Contains("Mooncap")&&!id.Contains("HerbalExtract"),"rune plant ingredient removed "+n);if(id==(n.Contains("Wand")?"resourceScrapLead":"resourceScrapIron"))metal=true;}Check(metal,"metal ingredient "+n);Check(ForestSliceCatalog.Rank(r)<=20,"updated exact recipe gate "+n);}}
  Check(runes==10,"all ten rune variants checked");Check(CraftingManager.GetAllRecipes().Exists(r=>r.GetName()=="delveTotemRune"&&r.craftingArea=="delveFieldCraftingMat"&&r.ingredients.Exists(i=>i.itemValue.ItemClass.GetItemName()=="resourceCropChrysanthemumPlant")),"totem flowers retained");
  SdtdConsole.Instance.Output("[Batch11Storage] PASS "+checks+" backend checks: storage boundaries, permissions, split consumption, refund records, insufficient funds, ten rune variants and totem preservation. UI acceptance remains a human playtest.");
 }catch(Exception e){SdtdConsole.Instance.Output("[Batch11Storage] FAIL "+e);}finally{NearbyCrafting.Station=null;if(p!=null)UnityEngine.Object.Destroy(p.gameObject);}}
}
