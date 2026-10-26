$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root 'playtest/ForestAccess20'
$mod=Join-Path $profile 'Mods/BatchOneProbe'
New-Item -ItemType Directory -Path $mod -Force|Out-Null
'<xml><Name value="BatchOneProbe"/><DisplayName value="Isolated Batch 01 verification"/><Version value="1.0"/><Author value="Delve"/></xml>'|Set-Content (Join-Path $mod 'ModInfo.xml')
$managed='D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','MemoryPack.dll','Unity.Addressables.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','UnityEngine.PhysicsModule.dll','UnityEngine.ImageConversionModule.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $profile 'Mods/Delve/Delve.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'BatchOneProbe.dll')) $refs (Join-Path $root 'tools/forest/BatchOneProbe.cs') (Join-Path $root 'tools/forest/BatchWagonFlow.cs')
if($LASTEXITCODE -ne 0){throw 'Batch probe compilation failed'}
Copy-Item (Join-Path $root 'artifacts/batch-01/vehicles.xml') $mod -Force


