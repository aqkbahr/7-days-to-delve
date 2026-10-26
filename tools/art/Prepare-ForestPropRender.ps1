param([switch]$Start)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$profile=Join-Path $root 'artifacts\forest-props\RenderProfile'
$mod=Join-Path $profile 'Mods\ForestPropRenderProbe'
New-Item -ItemType Directory -Path (Join-Path $mod 'Resources') -Force|Out-Null
Copy-Item (Join-Path $root 'artifacts\forest-props\Bundle\forestprops.unity3d') (Join-Path $mod 'Resources') -Force
Copy-Item (Join-Path $root 'artifacts\forest-props\UnityProject\Assets\build-input.json') $profile -Force
'<xml><Name value="ForestPropRenderProbe"/><DisplayName value="Isolated station plant and item art renderer"/><Version value="1.0.0"/><Author value="Delve"/></xml>'|Set-Content (Join-Path $mod 'ModInfo.xml')
$game='D:\Steam\steamapps\common\7 Days To Die';$managed=Join-Path $game '7DaysToDie_Data\Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.AnimationModule.dll','UnityEngine.PhysicsModule.dll','UnityEngine.ImageConversionModule.dll','UnityEngine.ParticleSystemModule.dll','UnityEngine.JSONSerializeModule.dll','Newtonsoft.Json.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll','Unity.Addressables.dll','Unity.ResourceManager.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'ForestPropRenderProbe.dll')) $refs (Join-Path $PSScriptRoot 'ForestPropRenderProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Prop probe compilation failed'}
if($Start){
 'RUNNING'|Set-Content (Join-Path $profile 'render-result.txt')
 $env:SteamAppId='251570';$env:SteamGameId='251570'
 $args=@('-batchmode','-noeac','-skipintro',('-UserDataFolder="'+$profile+'"'),'-logfile',('"'+(Join-Path $profile 'game.log')+'"'))
 $p=Start-Process (Join-Path $game '7DaysToDie.exe') -ArgumentList $args -WindowStyle Hidden -PassThru
 $p.Id|Set-Content (Join-Path $profile 'probe.pid');Write-Output ('Prop render process '+$p.Id)
}




