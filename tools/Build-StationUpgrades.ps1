$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$base=(Get-Content (Join-Path $root 'artifacts/station-upgrades/base.txt') -Raw).Trim()
$game='D:/Steam/steamapps/common/7 Days To Die'
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $game 'Mods/0_TFP_Harmony/0Harmony.dll')
$refs+='/reference:'+(Join-Path $base 'Mods/Delve/Delve.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library /optimize+ ('/out:'+(Join-Path $root 'src/ZZZZZZZZZZDelveStations/DelveStations.dll')) $refs (Get-ChildItem (Join-Path $root 'src/StationUpgrades') -Filter '*.cs'|ForEach-Object FullName)
if($LASTEXITCODE -ne 0){throw 'Station upgrade build failed'}
