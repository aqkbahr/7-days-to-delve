$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$managed='D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','LogLibrary.dll','netstandard.dll','MemoryPack.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$output=Join-Path $root ('artifacts/batch-02/SaveWorker_'+[DateTime]::UtcNow.Ticks+'.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+$output) $refs (Join-Path $PSScriptRoot 'forest/BatchTwoSaveWorker.cs')
if($LASTEXITCODE -ne 0){throw 'Save worker compile failed'}
Copy-Item $output (Join-Path $root 'playtest/BatchTwoSave/Mods/BatchTwoSaveTools/Worker.dll') -Force
