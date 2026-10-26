using System;
using Delve;
class Rank20Tests {
 static int checks;
 static void Check(bool condition,string label){checks++;if(!condition)throw new Exception(label);}
 static void Main(){
  Check(!Rank20Rules.LongRange(2.09f,3),"inside polearm outer zone");
  Check(Rank20Rules.LongRange(2.1f,3),"outer zone boundary");
  Check(Rank20Rules.LongRange(3,3),"maximum reach");
  Check(!Rank20Rules.LongRange(3.1f,3),"beyond reach");
  Check(!Rank20Rules.LongRange(0,0),"missing reach cannot qualify");
  Check(Math.Abs(Rank20Rules.CappedMovement(2,3,.15f)-2.3f)<.001f,"aim movement bonus");
  Check(Rank20Rules.CappedMovement(2.9f,3,.25f)==3,"combined aim cap");
  Check(!Rank20Rules.WardReady(true,true,7.99f,0),"ward delay");
  Check(Rank20Rules.WardReady(true,true,8,0),"ward exact ready time");
  Check(!Rank20Rules.WardReady(true,true,9,2),"hostile hit resets delay");
  Check(!Rank20Rules.WardReady(false,true,20,0)&&!Rank20Rules.WardReady(true,false,20,0),"equipment and life requirements");
  float carry=0;int total=0;for(int i=0;i<100;i++)total+=Rank20Rules.BonusOutput(1,.15f,ref carry);
  Check(total==115&&Math.Abs(carry)<.0001f,"small batches preserve exact extraction yield");
  carry=0;Check(Rank20Rules.BonusOutput(100,.15f,ref carry)==total,"batch size does not change yield");
  carry=.9f;Check(Rank20Rules.BonusOutput(0,.15f,ref carry)==0&&carry==.9f,"empty craft does not consume carry");
  Check(Rank20Rules.WoodCost(1)==1&&Rank20Rules.WoodCost(10)==9&&Rank20Rules.WoodCost(11)==10,"construction cost rounds conservatively");
  Console.WriteLine("PASS: "+checks+" rank-20 rule checks");
 }
}
