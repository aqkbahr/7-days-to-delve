param([string]$ProfileName='ForestUnifiedM3',[string]$SourceFile='')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$managed='D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed'
$mod=Join-Path $root "playtest/$ProfileName/Mods/Delve"
$refs=@('mscorlib.dll','System.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.PhysicsModule.dll','UnityEngine.dll','netstandard.dll') | ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:D:/Steam/steamapps/common/7 Days To Die/Mods/0_TFP_Harmony/0Harmony.dll'
$refs+='/reference:'+(Join-Path $mod 'Delve.dll')
$source=if($SourceFile){(Resolve-Path -LiteralPath $SourceFile).Path}else{Join-Path $PSScriptRoot 'compatibility/SpellVisibility.cs'}
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'DelveSpellVisibility.dll')) $refs $source
if($LASTEXITCODE -ne 0){throw 'Visibility compatibility compilation failed'}
