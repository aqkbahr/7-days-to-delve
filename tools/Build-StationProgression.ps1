param([string]$BaseRelease='')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if(!$BaseRelease){$BaseRelease=(Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim()}
$python='C:/Users/Michael/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $python (Join-Path $PSScriptRoot 'build_station_progression.py') --base $BaseRelease
if($LASTEXITCODE -ne 0){throw 'Station catalogue/dependency audit failed'}
$game='D:/Steam/steamapps/common/7 Days To Die'
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $game 'Mods/0_TFP_Harmony/0Harmony.dll')
$refs+='/reference:'+(Join-Path $BaseRelease 'Mods/Delve/Delve.dll')
$mod=Join-Path $root 'src/ZZZZZZZZZZDelveCraftingStations'
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library /optimize+ ('/out:'+(Join-Path $mod 'DelveCraftingStations.dll')) $refs (Join-Path $mod 'Catalog.generated.cs') (Join-Path $mod 'StationProgression.cs')
if($LASTEXITCODE -ne 0){throw 'Station progression compile failed'}

