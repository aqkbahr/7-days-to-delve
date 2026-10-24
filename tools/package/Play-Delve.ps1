param([string]$GamePath='')
$ErrorActionPreference='Stop'
try {
    $package=$PSScriptRoot
    if (!$GamePath) {
        $saved=Join-Path $package 'game-path.txt'
        if (Test-Path $saved) { $GamePath=(Get-Content $saved -Raw).Trim() }
    }
    if (!$GamePath) {
        foreach($candidate in @('D:/Steam/steamapps/common/7 Days To Die','C:/Program Files (x86)/Steam/steamapps/common/7 Days To Die')) {
            if (Test-Path (Join-Path $candidate '7DaysToDie.exe')) { $GamePath=$candidate; break }
        }
    }
    if (!$GamePath -or !(Test-Path (Join-Path $GamePath '7DaysToDie.exe'))) {
        $GamePath=Read-Host 'Paste your 7 Days to Die installation folder'
        $GamePath=$GamePath.Trim().Trim('"')
    }
    if (!(Test-Path (Join-Path $GamePath '7DaysToDie.exe'))) { throw 'Game executable not found in that folder.' }
    if (!(Test-Path (Join-Path $GamePath 'Mods/0_TFP_Harmony/ModInfo.xml'))) { throw 'The bundled TFP Harmony component is missing. This playtest requires the standard 3.3 installation.' }
    & (Join-Path $package 'Verify-Package.ps1')
    $GamePath | Set-Content (Join-Path $package 'game-path.txt') -Encoding utf8
    $data=Join-Path $package 'PlaytestData'
    $mods=Join-Path $data 'Mods'
    $logs=Join-Path $data 'logs'
    New-Item -ItemType Directory -Path $mods,$logs -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $package 'Mods/Delve') -Destination $mods -Recurse -Force
    $log=Join-Path $logs ('client-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.log')
    $env:SteamAppId='251570'; $env:SteamGameId='251570'
    Write-Host 'Launching Delve with isolated saves and Easy Anti-Cheat disabled.'
    Write-Host 'Create a NEW world named DelveTest. Vanilla maps are intentional for this build.'
    Write-Host "Log: $log"
    # A separate argv element is required for Unity's -logfile switch.
    Start-Process -FilePath (Join-Path $GamePath '7DaysToDie.exe') -WorkingDirectory $GamePath -ArgumentList @('-noeac','-EACEnabled=false',('-UserDataFolder="'+$data+'"'),'-logfile',('"'+$log+'"'))
} catch {
    Write-Host $_ -ForegroundColor Red
    Read-Host 'Press Enter to close'
    exit 1
}
