param([switch]$HarnessOnly)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root 'playtest/ForestBestiary'
$pin=Join-Path $root 'artifacts/forest-base-release.txt'
$release=(Get-Content $(if(Test-Path $pin){$pin}else{Join-Path $root 'dist/latest-allium-release.txt'}) -Raw).Trim()
$game='D:/Steam/steamapps/common/7 Days To Die'
if(!$HarnessOnly) {
 if(Test-Path $profile){throw 'Fresh fixture profile already exists; use HarnessOnly to update its test DLL.'}
 New-Item -ItemType Directory -Path $profile,(Join-Path $profile 'Mods'),(Join-Path $profile 'GeneratedWorlds') -Force | Out-Null
 Copy-Item (Join-Path $release 'Mods/*') (Join-Path $profile 'Mods') -Recurse
 Copy-Item (Join-Path $release 'Worlds/*') (Join-Path $profile 'GeneratedWorlds') -Recurse
 [xml]$cfg=Get-Content (Join-Path $game 'serverconfig.xml')
 $settings=@{ServerName='Delve Forest Bestiary Fixture';ServerVisibility='0';ServerIP='127.0.0.1';ServerPort='28010';ServerPassword='delve-local-test';ServerMaxPlayerCount='4';ServerAllowCrossplay='false';EACEnabled='false';GameWorld=(Get-Content (Join-Path $release 'world-name.txt') -Raw).Trim();GameName='ForestBestiaryFixture';UserDataFolder=$profile;TelnetEnabled='true';TelnetPort='28019';TelnetPassword=[Guid]::NewGuid().ToString('N');WebDashboardEnabled='false';TerminalWindowEnabled='false'}
 foreach($s in $settings.GetEnumerator()){$p=$cfg.SelectSingleNode("/ServerSettings/property[@name='$($s.Key)']");if(!$p){$p=$cfg.CreateElement('property');$p.SetAttribute('name',$s.Key);$null=$cfg.DocumentElement.AppendChild($p)};$p.SetAttribute('value',$s.Value)}
 $cfg.Save((Join-Path $profile 'serverconfig.xml'))
 @{GamePath=$game;ProfilePath=$profile}|ConvertTo-Json|Set-Content (Join-Path $profile 'profile.json')
}
Copy-Item (Join-Path $root 'src/ZDelveForest') (Join-Path $profile 'Mods') -Recurse -Force
$mod=Join-Path $profile 'Mods/ForestProbe';New-Item -ItemType Directory -Path $mod -Force|Out-Null
'<xml><Name value="ForestProbe"/><DisplayName value="Isolated Forest probe"/><Version value="0.1.0"/><Author value="Delve"/></xml>'|Set-Content (Join-Path $mod 'ModInfo.xml')
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.AnimationModule.dll','UnityEngine.dll','MemoryPack.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $profile 'Mods/Delve/Delve.dll');$refs+='/reference:'+(Join-Path $root 'src/ZDelveForest/DelveForest.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'ForestProbe.dll')) $refs (Join-Path $PSScriptRoot 'forest/ForestProbe.cs') (Join-Path $PSScriptRoot 'incursion/IncursionProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Forest probe compilation failed'}
