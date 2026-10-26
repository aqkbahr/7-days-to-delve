$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
& 'C:\Users\Michael\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' (Join-Path $PSScriptRoot 'stage_native_foundation.py')
if($LASTEXITCODE -ne 0){throw 'Staging failed'}
$runtime='D:\AlliumArt\QualityPass20261025\Runtime'
$game='D:\Steam\steamapps\common\7 Days To Die'
$managed=Join-Path $game '7DaysToDie_Data\Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.AnimationModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll','Unity.Addressables.dll','Unity.ResourceManager.dll','UnityEngine.ParticleSystemModule.dll','UnityEngine.PhysicsModule.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $game 'Mods\0_TFP_Harmony\0Harmony.dll')
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /noconfig /nostdlib+ /target:library /optimize+ ('/out:'+(Join-Path $runtime 'DelvePresentation.dll')) $refs (Get-ChildItem -LiteralPath $runtime -Filter '*.cs' | ForEach-Object FullName)
if($LASTEXITCODE -ne 0){throw 'Staged presentation compilation failed'}
Get-FileHash (Join-Path $runtime 'DelvePresentation.dll') -Algorithm SHA256
