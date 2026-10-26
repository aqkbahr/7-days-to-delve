param([string]$ProfileName='HealingTotem',[string]$GamePath='D:/Steam/steamapps/common/7 Days To Die')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$mod=Join-Path $root "playtest/$ProfileName/Mods/HealingProbe"
New-Item -ItemType Directory -Path $mod -Force | Out-Null
'<xml><Name value="HealingProbe"/><DisplayName value="Healing test fixture"/><Version value="0.1.0"/><Author value="Delve"/></xml>' | Set-Content (Join-Path $mod 'ModInfo.xml')
$managed=Join-Path $GamePath '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll') | ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $root "playtest/$ProfileName/Mods/Delve/Delve.dll")
$refs+='/reference:'+(Join-Path $GamePath 'Mods/0_TFP_Harmony/0Harmony.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'HealingProbe.dll')) $refs (Join-Path $PSScriptRoot 'healing/HealingProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Healing probe compile failed'}
