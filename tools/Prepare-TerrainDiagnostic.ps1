param([string]$ProfileName='ForestTerrain')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$game='D:/Steam/steamapps/common/7 Days To Die'
$mod=Join-Path $root "playtest/$ProfileName/Mods/TerrainDiagnostic"
New-Item -ItemType Directory $mod -Force | Out-Null
'<xml><Name value="TerrainDiagnostic"/><DisplayName value="Terrain Diagnostic"/><Version value="1.0.0"/><Author value="Delve"/></xml>' | Set-Content (Join-Path $mod 'ModInfo.xml')
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll') | ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $game 'Mods/0_TFP_Harmony/0Harmony.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'TerrainDiagnostic.dll')) $refs (Join-Path $PSScriptRoot 'forest/TerrainDiagnostic.cs')
if($LASTEXITCODE -ne 0){throw 'Diagnostic compile failed'}
