$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$game='D:/Steam/steamapps/common/7 Days To Die'
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$mod=Join-Path $root 'playtest/ForestIntegrationClient/Mods/ClientIntegrationDriver'
New-Item -ItemType Directory -Path $mod -Force|Out-Null
'<xml><Name value="ClientIntegrationDriver"/><DisplayName value="Disposable local integration API"/><Version value="0.1.0"/><Author value="Delve"/></xml>'|Set-Content (Join-Path $mod 'ModInfo.xml')
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','MemoryPack.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'ClientIntegrationDriver.dll')) $refs (Join-Path $PSScriptRoot 'forest/ClientIntegrationDriver.cs')
if($LASTEXITCODE -ne 0){throw 'Client integration API compilation failed'}
