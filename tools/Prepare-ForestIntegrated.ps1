param([switch]$HarnessOnly,[string]$ProfileName='ForestIntegrated',[string]$Release='')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if($ProfileName -notmatch '^[A-Za-z0-9_-]+$'){throw 'Invalid profile name'}
$profile=Join-Path $root ('playtest/'+$ProfileName)
$release=if($Release){$Release}else{(Get-Content (Join-Path $root 'artifacts/forest-integrated-base.txt') -Raw).Trim()}
$game='D:/Steam/steamapps/common/7 Days To Die'
$pidFile=Join-Path $profile 'server.pid'
if(Test-Path $pidFile){$serverProcessId=[int](Get-Content $pidFile -Raw);$recordedProcess=Get-Process -Id $serverProcessId -ErrorAction SilentlyContinue;if($recordedProcess -and $recordedProcess.ProcessName -eq '7DaysToDie'){throw 'Stop the isolated server before replacing its loaded assemblies'}}
if(!$HarnessOnly) {
 if(Test-Path $profile){throw 'Profile exists; use HarnessOnly'}
 & (Join-Path $release 'Verify-Package.ps1')
 New-Item -ItemType Directory -Path $profile,(Join-Path $profile 'Mods'),(Join-Path $profile 'GeneratedWorlds') -Force|Out-Null
 Copy-Item (Join-Path $release 'Mods/*') (Join-Path $profile 'Mods') -Recurse
 Copy-Item (Join-Path $release 'Worlds/*') (Join-Path $profile 'GeneratedWorlds') -Recurse
 [xml]$cfg=Get-Content (Join-Path $game 'serverconfig.xml')
 $settings=@{ServerName='Delve Integrated Forest Fixture';ServerVisibility='0';ServerIP='127.0.0.1';ServerPort='28110';ServerPassword='delve-local-test';ServerMaxPlayerCount='4';ServerAllowCrossplay='false';EACEnabled='false';GameWorld=(Get-Content (Join-Path $release 'world-name.txt') -Raw).Trim();GameName=$ProfileName;UserDataFolder=$profile;TelnetEnabled='true';TelnetPort='28119';TelnetPassword=[Guid]::NewGuid().ToString('N');WebDashboardEnabled='false';TerminalWindowEnabled='false'}
 foreach($s in $settings.GetEnumerator()){$p=$cfg.SelectSingleNode("/ServerSettings/property[@name='$($s.Key)']");if(!$p){$p=$cfg.CreateElement('property');$p.SetAttribute('name',$s.Key);$null=$cfg.DocumentElement.AppendChild($p)};$p.SetAttribute('value',$s.Value)}
 $cfg.Save((Join-Path $profile 'serverconfig.xml'))
 @{GamePath=$game;ProfilePath=$profile}|ConvertTo-Json|Set-Content (Join-Path $profile 'profile.json')
}
if(!$Release){Copy-Item (Join-Path $root 'src/ZDelveForest') (Join-Path $profile 'Mods') -Recurse -Force}
$mod=Join-Path $profile 'Mods/ForestProbe';New-Item -ItemType Directory -Path $mod -Force|Out-Null
'<xml><Name value="ForestProbe"/><DisplayName value="Integrated Forest probe"/><Version value="0.2.0"/><Author value="Delve"/></xml>'|Set-Content (Join-Path $mod 'ModInfo.xml')
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.AnimationModule.dll','UnityEngine.dll','MemoryPack.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $profile 'Mods/Delve/Delve.dll');$refs+='/reference:'+(Join-Path $profile 'Mods/ZDelveForest/DelveForest.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'ForestProbe.dll')) $refs (Join-Path $PSScriptRoot 'forest/ForestProbe.cs') (Join-Path $PSScriptRoot 'forest/IntegratedProbe.cs') (Join-Path $PSScriptRoot 'incursion/IncursionProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Integrated probe compilation failed'}
