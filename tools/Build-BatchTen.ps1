$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$managed='D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed'
$mod=Join-Path $root 'src/ZZZZZZZZZZZZZZZDelveBatch10'
& (Join-Path $PSScriptRoot 'Build-Code.ps1') -OutputPath (Join-Path $root 'playtest/BatchTen/Mods/Delve/Delve.dll')
& (Join-Path $PSScriptRoot 'Build-Presentation.ps1')
Copy-Item (Join-Path $root 'src/ZDelvePresentation/DelvePresentation.dll') (Join-Path $root 'playtest/BatchTen/Mods/ZDelvePresentation/DelvePresentation.dll') -Force
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.AnimationModule.dll','UnityEngine.PhysicsModule.dll','UnityEngine.AssetBundleModule.dll','UnityEngine.ParticleSystemModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll','Unity.Addressables.dll','Unity.ResourceManager.dll')|ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:D:/Steam/steamapps/common/7 Days To Die/Mods/0_TFP_Harmony/0Harmony.dll'
$refs+='/reference:'+(Join-Path $root 'playtest/BatchTen/Mods/Delve/Delve.dll')
$refs+='/reference:'+(Join-Path $root 'src/ZDelvePresentation/DelvePresentation.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library /optimize+ ('/out:'+(Join-Path $mod 'DelveBatchTen.dll')) $refs (Get-ChildItem $mod -Filter '*.cs'|ForEach-Object FullName)
if($LASTEXITCODE -ne 0){throw 'Batch 10 compile failed'}
Copy-Item $mod (Join-Path $root 'playtest/BatchTen/Mods') -Recurse -Force
