$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$managed='D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.PhysicsModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll','MemoryPack.dll')|ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $root 'artifacts/summoning-20/Delve.dll')
$refs+='/reference:D:/Steam/steamapps/common/7 Days To Die/Mods/0_TFP_Harmony/0Harmony.dll'
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $root 'playtest/Summoning20/Mods/StationProbe/SummoningProbe.dll')) $refs (Join-Path $root 'tools/forest/SummoningProbe.cs') (Join-Path $root 'tools/forest/SummoningTwentyProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Summoning20 probe compile failed'}
