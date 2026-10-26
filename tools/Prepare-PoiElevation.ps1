$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$release=(Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim()
$profile=Join-Path $root 'playtest/PoiElevation'
$game='D:/Steam/steamapps/common/7 Days To Die'
$release|Set-Content (Join-Path $profile 'base-release.txt')
Copy-Item (Join-Path $release 'Mods') $profile -Recurse -Force
New-Item -ItemType Directory (Join-Path $profile 'GeneratedWorlds') -Force|Out-Null
Copy-Item (Join-Path $release 'Worlds/*') (Join-Path $profile 'GeneratedWorlds') -Recurse -Force
[xml]$cfg=Get-Content (Join-Path $game 'serverconfig.xml')
$settings=@{ServerName='POI elevation fixture';ServerVisibility='0';ServerIP='127.0.0.1';ServerPort='29250';ServerPassword='delve-local-test';ServerMaxPlayerCount='1';ServerAllowCrossplay='false';EACEnabled='false';GameWorld='Allium-v0.10';GameName='PoiElevation';UserDataFolder=$profile;TelnetEnabled='true';TelnetPort='29259';TelnetPassword=[Guid]::NewGuid().ToString('N');WebDashboardEnabled='false';TerminalWindowEnabled='false'}
foreach($s in $settings.GetEnumerator()){$p=$cfg.SelectSingleNode("/ServerSettings/property[@name='$($s.Key)']");if(!$p){$p=$cfg.CreateElement('property');$p.SetAttribute('name',$s.Key);$null=$cfg.DocumentElement.AppendChild($p)};$p.SetAttribute('value',$s.Value)}
$cfg.Save((Join-Path $profile 'serverconfig.xml'))
@{GamePath=$game;ProfilePath=$profile}|ConvertTo-Json|Set-Content (Join-Path $profile 'profile.json')
$mod=Join-Path $profile 'Mods/PoiElevationProbe';New-Item -ItemType Directory $mod -Force|Out-Null
'<xml><Name value="PoiElevationProbe"/><DisplayName value="POI Elevation Probe"/><Version value="1.0"/><Author value="Delve"/><Description value="Read-only elevation survey"/></xml>'|Set-Content (Join-Path $mod 'ModInfo.xml')
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll','MemoryPack.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'PoiElevationProbe.dll')) $refs (Join-Path $PSScriptRoot 'forest/PoiElevationProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Probe compilation failed'}
