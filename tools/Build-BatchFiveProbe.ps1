$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root 'playtest/BatchFive'
if(Test-Path (Join-Path $profile 'server.pid')){$serverId=[int](Get-Content (Join-Path $profile 'server.pid'));$proc=Get-Process -Id $serverId -ErrorAction SilentlyContinue;if($proc -and $proc.ProcessName -eq '7DaysToDie'){throw 'Stop BatchFive test server before compiling'}}
$managed='D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.PhysicsModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $profile 'Mods/Delve/Delve.dll')
$refs+='/reference:'+(Join-Path $managed 'Unity.Addressables.dll')
$refs+='/reference:'+(Join-Path $managed 'Unity.ResourceManager.dll')
$refs+='/reference:'+(Join-Path $managed 'UnityEngine.AssetBundleModule.dll')
$refs+='/reference:'+(Join-Path $profile 'Mods/ZZZZZZZZZZZDelveBatch05/DelveBatchFive.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $profile 'Mods/StationProbe/StationProbe.dll')) $refs (Join-Path $root 'artifacts/batch-05/BatchFiveStationProbe.cs') (Join-Path $root 'tools/forest/BatchFiveProbe.cs') (Join-Path $root 'tools/forest/BatchFourProbe.cs') (Join-Path $root 'artifacts/batch-05/MatPersistenceProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Batch five probe compile failed'}
