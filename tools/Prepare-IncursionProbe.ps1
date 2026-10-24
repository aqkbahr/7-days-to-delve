param([string]$ProfileName='FirstIncursion',[string]$GamePath='D:/Steam/steamapps/common/7 Days To Die')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$mod=Join-Path $root "playtest/$ProfileName/Mods/IncursionProbe"
New-Item -ItemType Directory -Path $mod -Force | Out-Null
'<xml><Name value="IncursionProbe"/><DisplayName value="Isolated incursion test harness"/><Version value="0.1.0"/><Author value="Delve"/></xml>' | Set-Content (Join-Path $mod 'ModInfo.xml')
$managed=Join-Path $GamePath '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll') | ForEach-Object { '/reference:'+(Join-Path $managed $_) }
$refs+='/reference:'+(Join-Path $root 'src/Delve/Delve.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'IncursionProbe.dll')) $refs (Join-Path $PSScriptRoot 'incursion/IncursionProbe.cs')
if($LASTEXITCODE -ne 0) { throw 'Probe compilation failed' }
Copy-Item (Join-Path $root 'src/Delve') (Join-Path $root "playtest/$ProfileName/Mods") -Recurse -Force
