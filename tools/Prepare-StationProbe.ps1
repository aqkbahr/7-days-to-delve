$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$mod=Join-Path $root 'playtest/StationUpgrades/Mods/StationProbe'
New-Item -ItemType Directory $mod -Force | Out-Null
'<xml><Name value="StationProbe"/><DisplayName value="Station upgrade diagnostic"/><Version value="1.0.0"/><Author value="Delve"/></xml>' | Set-Content (Join-Path $mod 'ModInfo.xml')
$base=(Get-Content (Join-Path $root 'artifacts/station-upgrades/base.txt') -Raw).Trim()
$game='D:/Steam/steamapps/common/7 Days To Die'
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $base 'Mods/Delve/Delve.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'StationProbe.dll')) $refs (Join-Path $PSScriptRoot 'forest/StationProbe.cs') (Join-Path $PSScriptRoot 'forest/AddonPersistenceProbe.cs') (Join-Path $PSScriptRoot 'forest/BatchFourProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Station probe compile failed'}
Copy-Item (Join-Path $root 'src/ZZZZZZZZZZDelveStations') (Join-Path $root 'playtest/StationUpgrades/Mods') -Recurse -Force
Copy-Item (Join-Path $root 'artifacts/station-upgrades/checks.xml') (Join-Path $mod 'addon-checks.xml') -Force
