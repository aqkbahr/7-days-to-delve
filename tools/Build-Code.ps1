param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die',[string]$OutputPath='',[string[]]$ExcludeSources=@())
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$managed=Join-Path $GamePath '7DaysToDie_Data/Managed'
$compiler=Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
if (!(Test-Path -LiteralPath $compiler)) { throw 'The .NET Framework C# compiler is required.' }
$output=if($OutputPath){[IO.Path]::GetFullPath($OutputPath)}else{Join-Path $root 'src/Delve/Delve.dll'}
$references=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','MemoryPack.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll') | ForEach-Object { '/reference:'+(Join-Path $managed $_) }
$references += '/reference:'+(Join-Path $GamePath 'Mods/0_TFP_Harmony/0Harmony.dll')
$references += '/reference:'+(Join-Path $managed 'UnityEngine.PhysicsModule.dll')
$references += '/reference:'+(Join-Path $GamePath 'Mods/0_TFP_Harmony/System.ValueTuple.dll')
& $compiler /nologo /noconfig /nostdlib+ /target:library /optimize+ /warn:4 ('/out:'+$output) $references (Get-ChildItem (Join-Path $root 'src/Code') -Filter '*.cs' | Where-Object {$_.Name -notin $ExcludeSources} | ForEach-Object FullName)
if ($LASTEXITCODE -ne 0) { throw 'Delve code compilation failed.' }
Write-Host "Compiled $output"


