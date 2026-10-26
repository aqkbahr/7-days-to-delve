$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$managed='D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.PhysicsModule.dll','UnityEngine.AssetBundleModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll','MemoryPack.dll')|ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $root 'playtest/BatchTen/Mods/Delve/Delve.dll')
$refs+='/reference:'+(Join-Path $root 'src/ZZZZZZZZZZZZZZZDelveBatch10/DelveBatchTen.dll')
$refs+='/reference:D:/Steam/steamapps/common/7 Days To Die/Mods/0_TFP_Harmony/0Harmony.dll'
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $root 'playtest/BatchTen/Mods/StationProbe/BatchTenProbe.dll')) $refs (Join-Path $root 'tools/forest/BatchTenProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Probe compile failed'}
