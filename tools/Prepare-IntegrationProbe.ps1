param([switch]$StageOnly)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$game='D:/Steam/steamapps/common/7 Days To Die'
$profile=Join-Path $root 'playtest/ForestIntegration'
$probe=Join-Path $profile 'Mods/IntegrationProbe'
New-Item -ItemType Directory -Path $probe -Force|Out-Null
if(!$StageOnly){Copy-Item (Join-Path $root 'src/ZDelvePresentation') (Join-Path $profile 'Mods') -Recurse -Force}
'<xml><Name value="IntegrationProbe"/><DisplayName value="Disposable integration tests"/><Version value="0.1.0"/><Author value="Delve"/></xml>'|Set-Content (Join-Path $probe 'ModInfo.xml')
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','MemoryPack.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $profile 'Mods/Delve/Delve.dll')
$refs+='/reference:'+(Join-Path $profile 'Mods/ZDelvePresentation/DelvePresentation.dll')
$refs+=@('UnityEngine.PhysicsModule.dll','UnityEngine.AnimationModule.dll','UnityEngine.ImageConversionModule.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$output=Join-Path $probe 'IntegrationProbe.dll'
if($StageOnly){$output=Join-Path $root 'artifacts/integration/IntegrationProbe.dll'}
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+$output) $refs (Join-Path $PSScriptRoot 'forest/Rank20Probe.cs') (Join-Path $PSScriptRoot 'forest/PresentationProbe.cs') (Join-Path $PSScriptRoot 'forest/Rank20CombatProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Integration probe compilation failed'}
