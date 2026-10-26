$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$release=(Get-Content (Join-Path $root 'artifacts/validation/station-progression/candidate.txt') -Raw).Trim()
$profile=Join-Path $root 'playtest/StationProgression'
$game='D:/Steam/steamapps/common/7 Days To Die'
if(Test-Path $profile){throw 'Use a new isolated profile; do not overwrite saves'}
& (Join-Path $release 'Verify-Package.ps1')
New-Item -ItemType Directory $profile|Out-Null
# Immutable assets share disk storage; neither the harness nor acceptance writes them.
foreach($folder in @('Mods','Worlds')){
 foreach($file in Get-ChildItem (Join-Path $release $folder) -Recurse -File){
  $rel=$file.FullName.Substring($release.Length+1)
  if($folder -eq 'Worlds'){$rel='GeneratedWorlds'+$rel.Substring(6)}
  $target=Join-Path $profile $rel
  New-Item -ItemType Directory (Split-Path $target) -Force|Out-Null
  New-Item -ItemType HardLink -Path $target -Target $file.FullName|Out-Null
 }
}
[xml]$cfg=Get-Content (Join-Path $game 'serverconfig.xml')
$settings=@{ServerName='Crafting Station Verification';ServerVisibility='0';ServerIP='127.0.0.1';ServerPort='29010';ServerPassword='delve-local-test';ServerMaxPlayerCount='4';ServerAllowCrossplay='false';EACEnabled='false';GameWorld='Allium-v0.10';GameName='StationProgression';UserDataFolder=$profile;TelnetEnabled='true';TelnetPort='29019';TelnetPassword=[Guid]::NewGuid().ToString('N');WebDashboardEnabled='false';TerminalWindowEnabled='false'}
foreach($s in $settings.GetEnumerator()){$p=$cfg.SelectSingleNode("/ServerSettings/property[@name='$($s.Key)']");if(!$p){$p=$cfg.CreateElement('property');$p.SetAttribute('name',$s.Key);$null=$cfg.DocumentElement.AppendChild($p)};$p.SetAttribute('value',$s.Value)}
$cfg.Save((Join-Path $profile 'serverconfig.xml'))
@{GamePath=$game;ProfilePath=$profile}|ConvertTo-Json|Set-Content (Join-Path $profile 'profile.json')
$mod=Join-Path $profile 'Mods/StationProbe';New-Item -ItemType Directory $mod|Out-Null
'<xml><Name value="StationProbe"/><DisplayName value="Station verification"/><Version value="1.0"/><Author value="Delve"/></xml>'|Set-Content (Join-Path $mod 'ModInfo.xml')
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $profile 'Mods/Delve/Delve.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'StationProbe.dll')) $refs (Join-Path $root 'tools/forest/StationProgressionProbe.cs') (Join-Path $root 'tools/forest/StationPersistenceProbe.cs') (Join-Path $root 'tools/forest/BatchFourProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Station probe compilation failed'}
Copy-Item (Join-Path $root 'artifacts/validation/station-progression/slice-checks.xml') $mod
