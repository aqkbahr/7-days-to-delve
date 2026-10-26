param([switch]$Start)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$profile=Join-Path $root 'artifacts\thornback\RenderProfile'
$mod=Join-Path $profile 'Mods\ThornbackRenderProbe'
New-Item -ItemType Directory -Path $mod -Force|Out-Null
Copy-Item (Join-Path $root 'src\ZDelveThornbackArt') (Join-Path $profile 'Mods') -Recurse -Force
'<xml><Name value="ThornbackRenderProbe"/><DisplayName value="Isolated Thornback rendering probe"/><Version value="1.0.0"/><Author value="Delve"/></xml>'|Set-Content (Join-Path $mod 'ModInfo.xml')
$game='D:\Steam\steamapps\common\7 Days To Die';$managed=Join-Path $game '7DaysToDie_Data\Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.AnimationModule.dll','UnityEngine.PhysicsModule.dll','UnityEngine.ImageConversionModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll','Unity.Addressables.dll','Unity.ResourceManager.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $root 'src\ZDelveThornbackArt\ThornbackArt.dll')
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'ThornbackRenderProbe.dll')) $refs (Join-Path $PSScriptRoot 'ThornbackRenderProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Render probe compilation failed'}
if($Start){
 $env:SteamAppId='251570';$env:SteamGameId='251570'
 $arguments=@('-batchmode','-noeac','-skipintro',('-UserDataFolder="'+$profile+'"'),'-logfile',('"'+(Join-Path $profile 'game.log')+'"'))
 $p=Start-Process (Join-Path $game '7DaysToDie.exe') -ArgumentList $arguments -WindowStyle Hidden -PassThru
 $p.Id|Set-Content (Join-Path $profile 'probe.pid');Write-Output ('Render test process '+$p.Id)
}
