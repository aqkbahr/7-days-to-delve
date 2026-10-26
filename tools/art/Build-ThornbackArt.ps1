$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$game='D:\Steam\steamapps\common\7 Days To Die'
$managed=Join-Path $game '7DaysToDie_Data\Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.AnimationModule.dll','UnityEngine.PhysicsModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll','Unity.Addressables.dll','Unity.ResourceManager.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $game 'Mods\0_TFP_Harmony\0Harmony.dll')
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /noconfig /nostdlib+ /target:library /warn:4 ('/out:'+(Join-Path $root 'src\ZDelveThornbackArt\ThornbackArt.dll')) $refs (Join-Path $root 'src\Art\ThornbackPresentation.cs')
if($LASTEXITCODE -ne 0){throw 'Thornback art compilation failed'}
$destination=Join-Path $root 'src\ZDelveThornbackArt\Resources'
New-Item -ItemType Directory -Path $destination -Force|Out-Null
Copy-Item (Join-Path $root 'artifacts\thornback\Bundle\thornback.unity3d') $destination
