param([string]$GamePath='', [string]$DataPath='', [switch]$InstallOnly)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Hash-File.ps1')
try {
    if(Get-Process -Name 7DaysToDie,7DaysToDieServer -ErrorAction SilentlyContinue){throw 'Close 7 Days to Die and its server before installing or launching Delve.'}
    $package=[IO.Path]::GetFullPath($PSScriptRoot)
    $settingsPath=Join-Path $package 'launcher-settings.local.json'
    if(Test-Path -LiteralPath $settingsPath){
        $settings=Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
        if(!$GamePath){$GamePath=$settings.gamePath}
        if(!$DataPath){$DataPath=$settings.dataPath}
    }
    if(!$GamePath){
        $candidates=@('D:/Steam/steamapps/common/7 Days To Die',"${env:ProgramFiles(x86)}/Steam/steamapps/common/7 Days To Die")
        $steam=(Get-ItemProperty 'HKCU:/Software/Valve/Steam' -ErrorAction SilentlyContinue).SteamPath
        if($steam){
            $candidates+=Join-Path $steam 'steamapps/common/7 Days To Die'
            $libraries=Join-Path $steam 'steamapps/libraryfolders.vdf'
            if(Test-Path -LiteralPath $libraries){
                foreach($match in [regex]::Matches((Get-Content -LiteralPath $libraries -Raw),'"path"\s+"([^"]+)"')){
                    $candidates+=Join-Path ($match.Groups[1].Value.Replace('\\','\')) 'steamapps/common/7 Days To Die'
                }
            }
        }
        foreach($candidate in $candidates){if(Test-Path -LiteralPath (Join-Path $candidate '7DaysToDie.exe')){$GamePath=$candidate;break}}
    }
    if(!$GamePath){$GamePath=(Read-Host 'Paste your 7 Days to Die installation folder').Trim().Trim('"')}
    $GamePath=[IO.Path]::GetFullPath($GamePath)
    if(!(Test-Path -LiteralPath (Join-Path $GamePath '7DaysToDie.exe'))){throw 'Game executable not found. Supply -GamePath with the correct Steam installation folder.'}
    if(!$DataPath){$DataPath=Join-Path $env:LOCALAPPDATA '7DaysToDelve/UserData'}
    $DataPath=[IO.Path]::GetFullPath($DataPath).TrimEnd('\','/')
    foreach($protected in @($package,$GamePath)){
        $a=$DataPath+[IO.Path]::DirectorySeparatorChar;$b=$protected.TrimEnd('\','/')+[IO.Path]::DirectorySeparatorChar
        if($a.StartsWith($b,[StringComparison]::OrdinalIgnoreCase) -or $b.StartsWith($a,[StringComparison]::OrdinalIgnoreCase)){throw 'The Delve data folder must be separate from the game installation and extracted download.'}
    }
    & (Join-Path $package 'Verify-Package.ps1') -GamePath $GamePath
    $manifest=Get-Content -LiteralPath (Join-Path $package 'manifest.json') -Raw | ConvertFrom-Json
    $worldName=$manifest.worldName
    if($worldName -notmatch '^Allium-v[0-9.]+$'){throw 'Invalid world name in package.'}
    $world=Join-Path $DataPath ('GeneratedWorlds/'+$worldName)
    $worldEntries=@($manifest.files | Where-Object { $_.path.StartsWith('Worlds/') })
    if(Test-Path -LiteralPath $world){
        foreach($entry in $worldEntries){
            $target=Join-Path $DataPath ($entry.path.Replace('Worlds/','GeneratedWorlds/'))
            if(!(Test-Path -LiteralPath $target) -or (Get-DelveFileHash -LiteralPath $target).Hash -ne $entry.sha256){throw 'Existing Allium world differs from this release. Keep that profile intact and use a separate -DataPath for a new world.'}
        }
    }
    $mods=Join-Path $DataPath 'Mods'
    $expected=@(Get-ChildItem -LiteralPath (Join-Path $package 'Mods') -Directory | Select-Object -ExpandProperty Name)
    if(Test-Path -LiteralPath $mods){
        foreach($item in Get-ChildItem -LiteralPath $mods){if(!$item.PSIsContainer -or $item.Name -notin $expected){throw "Unrecognized content in this profile's Mods folder: $($item.Name). Use a separate Delve data folder; nothing was removed."}}
    }
    New-Item -ItemType Directory -Path $DataPath -Force | Out-Null
    $runtime=@($manifest.files | Where-Object { $_.path.StartsWith('Mods/') })
    $alreadyInstalled=(Test-Path -LiteralPath $mods)
    if($alreadyInstalled){
        $alreadyInstalled=@(Get-ChildItem -LiteralPath $mods -Recurse -File).Count -eq $runtime.Count
        foreach($entry in $runtime){
            $target=Join-Path $DataPath $entry.path
            if(!(Test-Path -LiteralPath $target) -or (Get-DelveFileHash -LiteralPath $target).Hash -ne $entry.sha256){$alreadyInstalled=$false;break}
        }
    }
    if(!$alreadyInstalled){
    $stage=Join-Path $DataPath ('.delve-staging-'+[Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $stage | Out-Null
    Copy-Item -LiteralPath (Join-Path $package 'Mods') -Destination $stage -Recurse
    foreach($entry in $manifest.files | Where-Object { $_.path.StartsWith('Mods/') }){
        if((Get-DelveFileHash -LiteralPath (Join-Path $stage $entry.path)).Hash -ne $entry.sha256){throw 'Staged mod copy failed verification. Existing mods and saves remain intact.'}
    }
    $backup=$null
    try {
        if(Test-Path -LiteralPath $mods){
            $backup=Join-Path $DataPath ('Backups/Mods-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,6))
            New-Item -ItemType Directory -Path (Split-Path $backup -Parent) -Force | Out-Null
            Move-Item -LiteralPath $mods -Destination $backup
        }
        Move-Item -LiteralPath (Join-Path $stage 'Mods') -Destination $mods
    } catch {
        if($backup -and !(Test-Path -LiteralPath $mods)){Move-Item -LiteralPath $backup -Destination $mods}
        throw
    }
    # Remove only the now-empty staging directory, never saves or recursive paths.
    Remove-Item -LiteralPath $stage
    }
    if(!(Test-Path -LiteralPath $world)){
        $worldStage=Join-Path $DataPath ('.delve-world-'+[Guid]::NewGuid().ToString('N'))
        Copy-Item -LiteralPath (Join-Path $package ('Worlds/'+$worldName)) -Destination $worldStage -Recurse
        foreach($entry in $worldEntries){
            $relative=$entry.path.Substring(('Worlds/'+$worldName+'/').Length)
            if((Get-DelveFileHash -LiteralPath (Join-Path $worldStage $relative)).Hash -ne $entry.sha256){throw 'Staged world copy failed verification.'}
        }
        New-Item -ItemType Directory -Path (Split-Path $world -Parent) -Force | Out-Null
        Move-Item -LiteralPath $worldStage -Destination $world
    }
    @{gamePath=$GamePath;dataPath=$DataPath} | ConvertTo-Json | Set-Content -LiteralPath $settingsPath -Encoding utf8
    $logs=Join-Path $DataPath 'logs';New-Item -ItemType Directory -Path $logs -Force | Out-Null
    ('-noeac -EACEnabled=false -UserDataFolder="'+$DataPath+'"') | Set-Content -LiteralPath (Join-Path $DataPath 'Steam-launch-options.txt') -Encoding utf8
    Write-Host "Alpha .10 installed. Saves: $DataPath"
    Write-Host 'Existing Allium-v0.10 saves may be continued. New players: create a game using Allium-v0.10.'
    if($InstallOnly){return}
    $env:SteamAppId='251570';$env:SteamGameId='251570'
    $log=Join-Path $logs ('client-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.log')
    Start-Process -FilePath (Join-Path $GamePath '7DaysToDie.exe') -WorkingDirectory $GamePath -ArgumentList @('-noeac','-EACEnabled=false',('-UserDataFolder="'+$DataPath+'"'),'-logfile',('"'+$log+'"'))
} catch {Write-Error $_;exit 1}
