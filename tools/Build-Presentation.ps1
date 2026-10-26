$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$game='D:/Steam/steamapps/common/7 Days To Die'
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.AnimationModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll','Unity.Addressables.dll','Unity.ResourceManager.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $game 'Mods/0_TFP_Harmony/0Harmony.dll')
$refs+='/reference:'+(Join-Path $managed 'UnityEngine.ParticleSystemModule.dll')
$refs+='/reference:'+(Join-Path $managed 'UnityEngine.PhysicsModule.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library /optimize+ ('/out:'+(Join-Path $root 'src/ZDelvePresentation/DelvePresentation.dll')) $refs (Join-Path $root 'src/Art/ForestPresentation.cs') (Join-Path $root 'src/Art/EnemyRigs.generated.cs') (Join-Path $root 'src/Art/HeldCatalog.generated.cs') (Join-Path $root 'src/Art/HeldPresentation.cs') (Join-Path $root 'src/Art/ForestEffects.cs')
if($LASTEXITCODE -ne 0){throw 'Presentation compilation failed'}

