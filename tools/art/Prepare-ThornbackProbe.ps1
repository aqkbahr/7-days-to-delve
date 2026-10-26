$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$game='D:\Steam\steamapps\common\7 Days To Die'
$profile=Join-Path $root 'playtest\ThornbackArt'
$mods=Join-Path $profile 'Mods'
New-Item -ItemType Directory -Path $mods -Force|Out-Null
foreach($name in @('Delve','ZDelveForest')){Copy-Item (Join-Path $root "playtest\ForestCombined10\Mods\$name") $mods -Recurse -Force}
& (Join-Path $PSScriptRoot 'Build-ThornbackArt.ps1')
Copy-Item (Join-Path $root 'src\ZDelveThornbackArt') $mods -Recurse -Force
$probe=Join-Path $mods 'ThornbackWorldProbe';New-Item -ItemType Directory -Path $probe -Force|Out-Null
'<xml><Name value="ThornbackWorldProbe"/><DisplayName value="Disposable Thornback world fixture"/><Version value="1.0.0"/><Author value="Delve"/></xml>'|Set-Content (Join-Path $probe 'ModInfo.xml')
$managed=Join-Path $game '7DaysToDie_Data\Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.AnimationModule.dll','UnityEngine.PhysicsModule.dll','UnityEngine.ImageConversionModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll','MemoryPack.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $mods 'ZDelveThornbackArt\ThornbackArt.dll')
$refs+='/reference:'+(Join-Path $mods 'ZDelveForest\DelveForest.dll')
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $probe 'ThornbackWorldProbe.dll')) $refs (Join-Path $PSScriptRoot 'ThornbackWorldProbe.cs')
if($LASTEXITCODE -ne 0){throw 'World probe compilation failed'}
if(!(Test-Path (Join-Path $profile 'serverconfig.xml'))){
 [xml]$config=Get-Content (Join-Path $game 'serverconfig.xml')
 $settings=@{ServerName='Isolated Thornback Art Test';ServerVisibility='0';ServerIP='127.0.0.1';ServerPort='28180';ServerMaxPlayerCount='2';ServerPassword='delve-local-test';ServerAllowCrossplay='false';EACEnabled='false';GameWorld='Navezgane';GameName='ThornbackArtFixture';UserDataFolder=$profile;TelnetEnabled='true';TelnetPort='28189';TelnetPassword=[Guid]::NewGuid().ToString('N');WebDashboardEnabled='false';TerminalWindowEnabled='false'}
 foreach($s in $settings.GetEnumerator()){$p=$config.SelectSingleNode("/ServerSettings/property[@name='$($s.Key)']");if(!$p){$p=$config.CreateElement('property');$p.SetAttribute('name',$s.Key);$null=$config.DocumentElement.AppendChild($p)};$p.SetAttribute('value',$s.Value)}
 $config.Save((Join-Path $profile 'serverconfig.xml'))
}
@{GamePath=$game;ProfilePath=$profile}|ConvertTo-Json|Set-Content (Join-Path $profile 'profile.json')
Write-Output 'Prepared isolated ThornbackArt profile.'
