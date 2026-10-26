$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$profile=Join-Path $root 'playtest\ThornbackArt'
$game='D:\Steam\steamapps\common\7 Days To Die'
$prior=Get-Content (Join-Path $profile 'server.pid') -ErrorAction SilentlyContinue
if($prior){$p=Get-Process -Id $prior -ErrorAction SilentlyContinue;if($p -and $p.ProcessName -eq '7DaysToDie'){throw 'Previous fixture process is still running'}}
$arguments=@('-quit','-batchmode','-noeac','-dedicated',('-UserDataFolder="'+$profile+'"'),('-configfile="'+(Join-Path $profile 'serverconfig.xml')+'"'),'-logfile',('"'+(Join-Path $profile 'server.log')+'"'))
$env:SteamAppId='251570';$env:SteamGameId='251570'
$p=Start-Process (Join-Path $game '7DaysToDie.exe') -ArgumentList $arguments -WorkingDirectory $game -WindowStyle Hidden -PassThru
$p.Id|Set-Content (Join-Path $profile 'server.pid');Write-Output ('Started graphics-enabled world fixture '+$p.Id)
