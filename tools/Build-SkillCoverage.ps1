$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$base=(Get-Content (Join-Path $root 'artifacts/skill-coverage-base.txt') -Raw).Trim()
$game='D:/Steam/steamapps/common/7 Days To Die'
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','MemoryPack.dll','netstandard.dll')|ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $game 'Mods/0_TFP_Harmony/0Harmony.dll')
$refs+='/reference:'+(Join-Path $base 'Mods/Delve/Delve.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $root 'src/ZZZZZZZZZDelveSkillCoverage/DelveSkillCoverage.dll')) $refs (Get-ChildItem (Join-Path $root 'src/SkillCoverage') -Filter '*.cs'|ForEach-Object FullName)
if($LASTEXITCODE -ne 0){throw 'Skill coverage compilation failed'}
