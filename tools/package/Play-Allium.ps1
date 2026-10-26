param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die')
$ErrorActionPreference='Stop'
try {
    $package=$PSScriptRoot
    $worldName=(Get-Content (Join-Path $package 'world-name.txt') -Raw).Trim()
    if($worldName -notin @('Allium-v0.2','Allium-v0.3','Allium-v0.4','Allium-v0.5','Allium-v0.6','Allium-v0.7','Allium-v0.8','Allium-v0.9','Allium-v0.10')) { throw 'Unexpected packaged world name' }
    if (!(Test-Path (Join-Path $GamePath '7DaysToDie.exe'))) { throw 'Set -GamePath to the installed 7 Days to Die 3.3 folder.' }
    & (Join-Path $package 'Verify-Package.ps1')
    $data=Join-Path $package 'PlaytestData'
    $world=Join-Path $data ('GeneratedWorlds/'+$worldName)
    New-Item -ItemType Directory -Path (Join-Path $data 'Mods'),(Join-Path $data 'logs') -Force | Out-Null
    if (!(Test-Path $world)) {
        New-Item -ItemType Directory -Path (Split-Path $world) -Force | Out-Null
        Copy-Item (Join-Path $package ('Worlds/'+$worldName)) $world -Recurse
    } else {
        # Never replace world inputs beneath an existing save.
        foreach($name in @('dtm.raw','biomes.png','prefabs.xml','spawnpoints.xml','splat3.png','splat4.png')) {
            if ((Get-FileHash (Join-Path $world $name)).Hash -ne (Get-FileHash (Join-Path $package "Worlds/$worldName/$name")).Hash) {
                throw 'Installed Allium terrain differs. Use a fresh extracted package for a new map revision.'
            }
        }
    }
    foreach($mod in Get-ChildItem (Join-Path $package 'Mods') -Directory) { Copy-Item $mod.FullName (Join-Path $data 'Mods') -Recurse -Force }
    $log=Join-Path $data ('logs/client-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.log')
    $env:SteamAppId='251570'; $env:SteamGameId='251570'
    Write-Host "Allium exploration alpha: select NEW GAME, world $worldName, and a new game name."
    Write-Host 'Read START-HERE.txt for this version and its playtest scope.'
    Start-Process -FilePath (Join-Path $GamePath '7DaysToDie.exe') -WorkingDirectory $GamePath -ArgumentList @('-noeac','-EACEnabled=false',('-UserDataFolder="'+$data+'"'),('-GameWorld='+$worldName),'-GameName=AlliumExpedition','-logfile',('"'+$log+'"'))
} catch {
    Write-Host $_ -ForegroundColor Red
    Read-Host 'Press Enter to close'
    exit 1
}


