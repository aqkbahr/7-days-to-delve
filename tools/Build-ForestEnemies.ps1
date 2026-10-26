param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die',[string]$BaseRelease='')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$buildArgs=@();if($BaseRelease){$buildArgs=@('--base-release',$BaseRelease)}
& 'C:/Users/Michael/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' (Join-Path $PSScriptRoot 'build_forest_enemies.py') @buildArgs
if($LASTEXITCODE -ne 0){throw 'Forest content generation failed'}
$managed=Join-Path $GamePath '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.AnimationModule.dll','UnityEngine.dll','MemoryPack.dll','LogLibrary.dll','netstandard.dll') | ForEach-Object { '/reference:'+(Join-Path $managed $_) }
$refs+='/reference:'+(Join-Path $GamePath 'Mods/0_TFP_Harmony/0Harmony.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library /warn:4 ('/out:'+(Join-Path $root 'src/ZDelveForest/DelveForest.dll')) $refs (Get-ChildItem (Join-Path $root 'src/Forest') -Filter '*.cs' | ForEach-Object FullName)
if($LASTEXITCODE -ne 0){throw 'Forest code compilation failed'}
