param([string]$ProfileName='ForestAccess20')
$ErrorActionPreference='Stop'
if($ProfileName -notmatch '^[A-Za-z0-9_-]+$'){throw 'Invalid profile'}
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root ('playtest/'+$ProfileName)
$pidFile=Join-Path $profile 'server.pid'
if(Test-Path $pidFile){$testProcess=Get-Process -Id ([int](Get-Content $pidFile -Raw)) -ErrorAction SilentlyContinue;if($testProcess -and $testProcess.ProcessName -eq '7DaysToDie'){throw 'Stop the isolated server before updating its probe'}}
$mod=Join-Path $profile 'Mods/AccessProbe'
New-Item -ItemType Directory -Path $mod -Force|Out-Null
'<xml><Name value="AccessProbe"/><DisplayName value="Access verification"/><Version value="1.0"/><Author value="Delve"/></xml>'|Set-Content (Join-Path $mod 'ModInfo.xml')
$managed='D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $profile 'Mods/Delve/Delve.dll')
$sources=@('forest/OnboardingProbe.cs','forest/Rank20Probe.cs','RecruitProbe.cs','allium/ForestReadinessProbe.cs')|ForEach-Object {Join-Path $PSScriptRoot $_}
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'AccessProbe.dll')) $refs $sources
if($LASTEXITCODE -ne 0){throw 'Access probe compilation failed'}

Copy-Item (Join-Path $root 'artifacts/validation/forest-ready/slice-checks.xml') (Join-Path $mod 'slice-checks.xml') -Force
