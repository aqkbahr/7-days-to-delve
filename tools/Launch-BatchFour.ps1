param([int[]]$OtherIsolatedTestPids=@())
# One-time launch after acceptance, restoring the display mode from the last
# playable client log rather than inheriting the isolated 1280x720 test window.
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$release=(Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim()
if(Get-Process 7DaysToDie -ErrorAction SilentlyContinue|Where-Object {$_.Id -notin $OtherIsolatedTestPids}){throw 'A playable or unverified game process is still running'}
$manifest=Get-Content (Join-Path $release 'manifest.json') -Raw|ConvertFrom-Json
if($manifest.version -ne '0.10.6-batch04'){throw 'Batch 04 has not been packaged'}
& (Join-Path $release 'Verify-Package.ps1')
$data=(Get-Content (Join-Path $release 'save-data-location.txt') -Raw).Trim();$worldName='Allium-v0.10'
foreach($name in @('dtm.raw','biomes.png','prefabs.xml','spawnpoints.xml','splat3.png','splat4.png')){
 if((Get-FileHash (Join-Path $data "GeneratedWorlds/$worldName/$name")).Hash -ne (Get-FileHash (Join-Path $release "Worlds/$worldName/$name")).Hash){throw "Installed world differs: $name"}
}
foreach($mod in Get-ChildItem (Join-Path $release 'Mods') -Directory){Copy-Item $mod.FullName (Join-Path $data 'Mods') -Recurse -Force}
$game='D:/Steam/steamapps/common/7 Days To Die'
$log=Join-Path $data ('logs/client-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.log')
$env:SteamAppId='251570';$env:SteamGameId='251570'
$arguments=@('-noeac','-EACEnabled=false',('-UserDataFolder="'+$data+'"'),('-GameWorld='+$worldName),'-GameName=ForestTest01','-screen-fullscreen','1','-window-mode','borderless','-screen-width','1600','-screen-height','900','-logfile',('"'+$log+'"'))
$process=Start-Process -FilePath (Join-Path $game '7DaysToDie.exe') -WorkingDirectory $game -ArgumentList $arguments -PassThru
@{pid=$process.Id;log=$log;release=$release;version=$manifest.version}|ConvertTo-Json|Set-Content (Join-Path $root 'artifacts/batch-04/launched.json')
Write-Output "Launched Batch 04 PID $($process.Id). Continue ForestTest01. Log: $log"

