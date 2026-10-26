param([switch]$HarnessOnly)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root 'playtest/WayrestRecruits'
$release=(Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim()
$game='D:/Steam/steamapps/common/7 Days To Die'
if(!$HarnessOnly){
 if(Test-Path $profile){throw 'Fixture already exists; use HarnessOnly after stopping its server.'}
 New-Item -ItemType Directory -Path $profile,(Join-Path $profile 'Mods'),(Join-Path $profile 'GeneratedWorlds') -Force|Out-Null
 Copy-Item (Join-Path $release 'Mods/*') (Join-Path $profile 'Mods') -Recurse
 Copy-Item (Join-Path $release 'Worlds/*') (Join-Path $profile 'GeneratedWorlds') -Recurse
 [xml]$cfg=Get-Content (Join-Path $game 'serverconfig.xml')
 $settings=@{ServerName='Isolated Wayrest recruits';ServerVisibility='0';ServerIP='127.0.0.1';ServerPort='28290';ServerPassword='delve-local-test';ServerMaxPlayerCount='2';ServerAllowCrossplay='false';EACEnabled='false';GameWorld=(Get-Content (Join-Path $release 'world-name.txt') -Raw).Trim();GameName='WayrestRecruitsFixture';UserDataFolder=$profile;TelnetEnabled='true';TelnetPort='28299';TelnetPassword=[Guid]::NewGuid().ToString('N');WebDashboardEnabled='false';TerminalWindowEnabled='false'}
 foreach($s in $settings.GetEnumerator()){$p=$cfg.SelectSingleNode("/ServerSettings/property[@name='$($s.Key)']");if(!$p){$p=$cfg.CreateElement('property');$p.SetAttribute('name',$s.Key);$null=$cfg.DocumentElement.AppendChild($p)};$p.SetAttribute('value',$s.Value)}
 $cfg.Save((Join-Path $profile 'serverconfig.xml'))
 @{GamePath=$game;ProfilePath=$profile}|ConvertTo-Json|Set-Content (Join-Path $profile 'profile.json')
}
Copy-Item (Join-Path $root 'src/Delve/Delve.dll') (Join-Path $profile 'Mods/Delve/Delve.dll') -Force
Copy-Item (Join-Path $root 'src/ZDelveRecruits') (Join-Path $profile 'Mods') -Recurse -Force
$mod=Join-Path $profile 'Mods/RecruitProbe';New-Item -ItemType Directory -Path $mod -Force|Out-Null
'<xml><Name value="RecruitProbe"/><DisplayName value="Disposable recruit fixture"/><Version value="0.1.0"/><Author value="Delve"/></xml>'|Set-Content (Join-Path $mod 'ModInfo.xml')
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $profile 'Mods/Delve/Delve.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'RecruitProbe.dll')) $refs (Join-Path $PSScriptRoot 'RecruitProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Recruit probe compilation failed'}
