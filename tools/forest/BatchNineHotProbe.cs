using System;using System.IO;using System.Reflection;using System.Collections.Generic;
// Disposable-profile development command. Never shipped in a release.
public class ConsoleCmdBatchNineHot:ConsoleCmdAbstract {
 public override string[] getCommands(){return new[]{"batch9run"};}public override string getDescription(){return "Load the latest isolated recovery worker.";}
 public override void Execute(List<string> args,CommandSenderInfo sender){try{if(!GameIO.GetUserGameDataDir().Replace('\\','/').EndsWith("/BatchNine"))throw new Exception("Isolated fixture only");string folder=ModManager.GetMod("StationProbe",true).Path;string name=File.ReadAllText(Path.Combine(folder,"worker-path.txt")).Trim();if(Path.GetFileName(name)!=name)throw new Exception("Worker path must stay in probe folder");var asm=Assembly.Load(File.ReadAllBytes(Path.Combine(folder,name)));var worker=(ConsoleCmdAbstract)Activator.CreateInstance(asm.GetType("ConsoleCmdBatchNine"));worker.Execute(args,sender);}catch(Exception e){SdtdConsole.Instance.Output("[Batch09Hot] FAIL "+e);}}
}
