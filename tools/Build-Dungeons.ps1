param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
& 'C:/Users/Michael/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' (Join-Path $PSScriptRoot 'build_forest_delves.py') --config
if($LASTEXITCODE -ne 0){throw 'Dungeon configuration failed'}
$managed=Join-Path $GamePath '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','MemoryPack.dll','netstandard.dll') | ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $GamePath 'Mods/0_TFP_Harmony/0Harmony.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $root 'src/ZDelveDungeons/ForestDelves.dll')) $refs (Join-Path $root 'src/Dungeons/ForestDelves.cs')
if($LASTEXITCODE -ne 0){throw 'Dungeon code compilation failed'}
