$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$mod=Join-Path $root 'src/ZZZZZZZZZZZZDelveBatch05World'
$managed='D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:D:/Steam/steamapps/common/7 Days To Die/Mods/0_TFP_Harmony/0Harmony.dll'
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library /optimize+ ('/out:'+(Join-Path $mod 'DelveBatchFiveWorld.dll')) $refs (Join-Path $mod 'WorldChanges.cs')
if($LASTEXITCODE -ne 0){throw 'World module compile failed'}
