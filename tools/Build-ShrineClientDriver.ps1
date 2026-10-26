$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$client=Join-Path $root 'playtest/ShrineClient'
$managed='D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','MemoryPack.dll','netstandard.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $client 'Mods/Delve/Delve.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $client 'Mods/ShrineClientDriver/ShrineClientDriver.dll')) $refs (Join-Path $PSScriptRoot 'ShrineClientDriver.cs')
if($LASTEXITCODE -ne 0){throw 'Shrine client fixture compilation failed'}
