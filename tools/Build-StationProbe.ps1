$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root 'playtest/StationProgression'
if(Test-Path (Join-Path $profile 'server.pid')){$idValue=[int](Get-Content (Join-Path $profile 'server.pid'));$running=Get-Process -Id $idValue -ErrorAction SilentlyContinue;if($running -and $running.ProcessName -eq '7DaysToDie'){throw 'Stop isolated server before replacing probe'}}
$managed='D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $profile 'Mods/Delve/Delve.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $profile 'Mods/StationProbe/StationProbe.dll')) $refs (Join-Path $root 'tools/forest/StationProgressionProbe.cs') (Join-Path $root 'tools/forest/StationPersistenceProbe.cs') (Join-Path $root 'tools/forest/BatchFourProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Station probe compilation failed'}
