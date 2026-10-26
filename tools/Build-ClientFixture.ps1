$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$managed='D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','MemoryPack.dll','LogLibrary.dll','netstandard.dll','Unity.Addressables.dll','Unity.ResourceManager.dll','UnityEngine.AnimationModule.dll','UnityEngine.PhysicsModule.dll','UnityEngine.ParticleSystemModule.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $root 'src/Delve/Delve.dll')
$refs+='/reference:'+(Join-Path $root 'src/ZDelvePresentation/DelvePresentation.dll')
$output=Join-Path $root ('playtest/ForestIntegrationClient/ClientFixture_'+[DateTime]::UtcNow.Ticks+'.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+$output) $refs (Join-Path $PSScriptRoot 'forest/ClientFixture.cs') (Join-Path $PSScriptRoot 'forest/EquipmentFixture.cs') (Join-Path $PSScriptRoot 'forest/Rank20ClientFixture.cs')
if($LASTEXITCODE -ne 0){throw 'Client fixture compilation failed'}
Copy-Item -LiteralPath $output -Destination (Join-Path $root 'playtest/ForestIntegrationClient/ClientFixture.dll') -Force


