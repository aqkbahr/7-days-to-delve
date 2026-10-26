param([switch]$Start)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$profile=Join-Path $root 'artifacts\forest-enemies\RenderProfile'
$mod=Join-Path $profile 'Mods\ForestEnemyRenderProbe'
New-Item -ItemType Directory -Path (Join-Path $mod 'Resources') -Force|Out-Null
Copy-Item (Join-Path $root 'artifacts\forest-enemies\Bundle\*.unity3d') (Join-Path $mod 'Resources') -Force
'<xml><Name value="ForestEnemyRenderProbe"/><DisplayName value="Isolated Forest enemy renderer"/><Version value="1.0.0"/><Author value="Delve"/></xml>'|Set-Content (Join-Path $mod 'ModInfo.xml')
$game='D:\Steam\steamapps\common\7 Days To Die';$managed=Join-Path $game '7DaysToDie_Data\Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.AnimationModule.dll','UnityEngine.PhysicsModule.dll','UnityEngine.ImageConversionModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll','Unity.Addressables.dll','Unity.ResourceManager.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'ForestEnemyRenderProbe.dll')) $refs (Join-Path $PSScriptRoot 'ForestEnemyRenderProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Probe compilation failed'}
if($Start){
 'RUNNING'|Set-Content (Join-Path $profile 'render-result.txt')
 $env:SteamAppId='251570';$env:SteamGameId='251570'
 $args=@('-batchmode','-noeac','-skipintro',('-UserDataFolder="'+$profile+'"'),'-logfile',('"'+(Join-Path $profile 'game.log')+'"'))
 $p=Start-Process (Join-Path $game '7DaysToDie.exe') -ArgumentList $args -WindowStyle Hidden -PassThru
 $p.Id|Set-Content (Join-Path $profile 'probe.pid');Write-Output ('Forest render process '+$p.Id)
}


