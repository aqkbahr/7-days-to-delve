using System;using System.IO;using System.Collections;using System.Collections.Generic;using UnityEngine;
public class ConsoleCmdBatchWagons:ConsoleCmdAbstract {
 public override string[] getCommands(){return new[]{"batchwagonflow"};}
 public override string getDescription(){return "Isolated live wagon storage/damage fixture.";}
 public override void Execute(List<string> a,CommandSenderInfo s){if(GameManager.Instance.World.GetPlayers().Count>0)throw new Exception("Empty test server required");new GameObject("WagonFlow").AddComponent<BatchWagonFlow>();SdtdConsole.Instance.Output("[BatchWagons] Started");}
}
public class BatchWagonFlow:MonoBehaviour {
 ChunkManager.ChunkObserver observer;Dictionary<Vector3i,BlockValue> originals=new Dictionary<Vector3i,BlockValue>();int checks;string output;
 void Check(bool v,string s){checks++;if(!v)throw new Exception(s);}
 IEnumerator Start(){output=Path.Combine(ModManager.GetMod("BatchOneProbe",true).Path,"Evidence/wagon-flow.txt");var run=Run();try{while(true){bool more;object value=null;try{more=run.MoveNext();if(more)value=run.Current;}catch(Exception ex){File.WriteAllText(output,"FAIL "+ex);yield break;}if(!more)break;yield return value;}File.WriteAllText(output,"PASS "+checks+" live checks: ordinary and wide wagon storage, all three sedan damage transitions, crumpled and burnt wreck assets. Native IDs retained. Scripted harvest-tool damage, not a player-operated salvage test.");}finally{Cleanup();}}
 void Set(Vector3i pos,BlockValue b){var w=GameManager.Instance.World;if(!originals.ContainsKey(pos))originals.Add(pos,w.GetBlock(pos));w.SetBlock(pos,b,false,false);}
 IEnumerator Run(){var w=GameManager.Instance.World;observer=GameManager.Instance.AddChunkObserver(new Vector3(-100,80,-100),false,4,3);float end=Time.realtimeSinceStartup+45;while(w.GetHeight(-100,-100)<=0&&Time.realtimeSinceStartup<end)yield return new WaitForSeconds(1);Check(w.GetHeight(-100,-100)>0,"terrain");int y=w.GetTerrainHeight(-100,-100)+1;
  for(int x=-4;x<=4;x++)for(int z=-5;z<=5;z++)Set(new Vector3i(x-100,y-1,z-100),Block.GetBlockValue("woodLogPillar100"));
  var pos=new Vector3i(-100,y,-100);
  foreach(string name in new[]{"cntCar03SedanDamage0Master","cntSedan3Wide01White","cntFrontCrumpledSedan01White","burntSedan01"}){
   Set(pos,Block.GetBlockValue(name));yield return new WaitForSeconds(.5f);var value=w.GetBlock(pos);Check(value.Block.GetBlockName()==name,"placement "+name+" actual="+value.Block.GetBlockName()+" at="+pos);
   if(name!="burntSedan01"){var te=w.GetTileEntity(pos) as TileEntityComposite;Check(te!=null,"container "+name);Check(te.GetFeature<TEFeatureStorage>()!=null,"loot storage "+name);Check(te.GetFeature<TEFeatureStorage>().lootListName=="cars","original loot list "+name);}
   if(name=="cntCar03SedanDamage0Master")for(int stage=0;stage<3;stage++){value=w.GetBlock(pos);Check(value.Block.GetBlockName()=="cntCar03SedanDamage"+stage+"Master","stage "+stage);value.Block.DamageBlock(w,new BlockValueRef(pos),value,value.Block.MaxDamage+1,-1,null,true,false);yield return new WaitForSeconds(.5f);var next=w.GetBlock(pos);Check(stage==2?next.isair:next.Block.GetBlockName()=="cntCar03SedanDamage"+(stage+1)+"Master","damage downgrade "+stage);}
   Set(pos,BlockValue.Air);yield return null;
  }
 }
 void Cleanup(){var w=GameManager.Instance.World;foreach(var kv in originals)w.SetBlock(kv.Key,kv.Value,false,false);if(observer!=null)GameManager.Instance.RemoveChunkObserver(observer);Destroy(gameObject);}
}
