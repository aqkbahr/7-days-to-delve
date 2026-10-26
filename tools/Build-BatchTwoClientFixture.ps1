$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$managed='D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','MemoryPack.dll','LogLibrary.dll','netstandard.dll','Unity.Addressables.dll','Unity.ResourceManager.dll','UnityEngine.AnimationModule.dll','UnityEngine.PhysicsModule.dll','UnityEngine.ParticleSystemModule.dll','UnityEngine.ImageConversionModule.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $root 'artifacts/batch-02/Delve.dll')
$refs+='/reference:'+(Join-Path $root 'src/ZDelvePresentation/DelvePresentation.dll')
$output=Join-Path $root ('playtest/ForestIntegrationClient/BatchFixture_'+[DateTime]::UtcNow.Ticks+'.dll')
$pantry=Join-Path $root 'artifacts/batch-02/PantryFixture.cs'
(Get-Content (Join-Path $PSScriptRoot 'allium/PantryTools.cs') -Raw).Replace('ModManager.GetMod("AlliumTools",true).Path','Path.Combine(GameIO.GetUserGameDataDir(),"BatchTwoTools")')|Set-Content $pantry
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+$output) $refs (Join-Path $PSScriptRoot 'forest/BatchTwoClientFixture.cs') (Join-Path $PSScriptRoot 'forest/BatchTwoPrefabTools.cs') (Join-Path $PSScriptRoot 'forest/BatchTwoUIFixture.cs') (Join-Path $PSScriptRoot 'forest/BatchTwoInteractionFixture.cs') (Join-Path $PSScriptRoot 'forest/BatchTwoFinalClientFixture.cs') $pantry
if($LASTEXITCODE -ne 0){throw 'Batch fixture compilation failed'}
Copy-Item $output (Join-Path $root 'playtest/ForestIntegrationClient/ClientFixture.dll') -Force
