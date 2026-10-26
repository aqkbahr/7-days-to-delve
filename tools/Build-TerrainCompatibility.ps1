param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$managed=Join-Path $GamePath '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll') | ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $GamePath 'Mods/0_TFP_Harmony/0Harmony.dll')
$output=Join-Path $root 'src/Delve/DelveTerrainCompatibility.dll'
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library /optimize+ /warn:4 ('/out:'+$output) $refs (Join-Path $root 'src/TerrainCompatibility/TerrainCompatibility.cs')
if($LASTEXITCODE -ne 0){throw 'Terrain compatibility build failed'}
Write-Host "Compiled $output"
