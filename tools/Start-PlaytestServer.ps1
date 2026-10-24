param([string]$ProfileName='LivingBorder')
$ErrorActionPreference='Stop'
if ($ProfileName -notmatch '^[A-Za-z0-9_-]+$') { throw 'Invalid profile name.' }
$root=Split-Path $PSScriptRoot -Parent
$profilePath=Join-Path $root ('playtest/'+$ProfileName)
$profile=Get-Content (Join-Path $profilePath 'profile.json') -Raw | ConvertFrom-Json
$exe=Join-Path $profile.GamePath '7DaysToDie.exe'
$config=Join-Path $profilePath 'serverconfig.xml'
$log=Join-Path $profilePath 'server.log'
$arguments=@('-quit','-batchmode','-nographics','-noeac',('-UserDataFolder="'+$profilePath+'"'),('-configfile="'+$config+'"'),'-logfile',('"'+$log+'"'),'-dedicated')
$existing=Get-Content (Join-Path $profilePath 'server.pid') -ErrorAction SilentlyContinue
if ($existing -and (Get-Process -Id $existing -ErrorAction SilentlyContinue)) { throw 'The recorded server process is still running.' }
$env:SteamAppId='251570'; $env:SteamGameId='251570'
$process=Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory $profile.GamePath -WindowStyle Hidden -PassThru
$process.Id | Set-Content (Join-Path $profilePath 'server.pid')
Write-Host "Started isolated server PID $($process.Id). Log: $log"
