param([string]$ProfileName='TomeTrading')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$game='D:/Steam/steamapps/common/7 Days To Die'
$mod=Join-Path $root "playtest/$ProfileName/Mods/TomeProbe"
New-Item -ItemType Directory $mod -Force | Out-Null
'<xml><Name value="TomeProbe"/><DisplayName value="Tome Trading Probe"/><Version value="1.0.0"/><Author value="Delve"/></xml>' | Set-Content (Join-Path $mod 'ModInfo.xml')
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll') | ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $game 'Mods/0_TFP_Harmony/0Harmony.dll')
$refs+='/reference:'+(Join-Path $root 'src/Delve/DelveTomeTrading.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'TomeProbe.dll')) $refs (Join-Path $PSScriptRoot 'forest/TomeTradingProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Diagnostic compile failed'}

