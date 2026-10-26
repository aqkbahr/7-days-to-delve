param([string]$ProfileName='AlliumFarming')
$ErrorActionPreference='Stop'
if($ProfileName -notmatch '^[A-Za-z0-9_-]+$'){throw 'Invalid profile name'}
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root ('playtest/'+$ProfileName)
if(!(Test-Path (Join-Path $profile 'integration-sources.json'))){throw 'Run Prepare-AlliumFarming.ps1 first'}
$pidFile=Join-Path $profile 'server.pid'
if(Test-Path $pidFile){$testProcessId=[int](Get-Content $pidFile);if(Get-Process -Id $testProcessId -ErrorAction SilentlyContinue){throw 'Stop this profile server before rebuilding'}}
$python='C:/Users/Michael/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $python (Join-Path $PSScriptRoot 'build_forest_catalogue.py') --mods (Join-Path $profile 'Mods')
if($LASTEXITCODE -ne 0){throw 'Catalogue build failed'}
& $python (Join-Path $PSScriptRoot 'validate_forest_catalogue.py') --mods (Join-Path $profile 'Mods')
if($LASTEXITCODE -ne 0){throw 'Catalogue validation failed'}
Copy-Item -LiteralPath (Join-Path $root 'src/Code/ForestRecipeOwnership.generated.cs') -Destination (Join-Path $profile 'CodeSnapshot/ForestRecipeOwnership.generated.cs') -Force
$game='D:/Steam/steamapps/common/7 Days To Die';$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll') | ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $game 'Mods/0_TFP_Harmony/0Harmony.dll')
$refs+='/reference:'+(Join-Path $game 'Mods/0_TFP_Harmony/System.ValueTuple.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library /optimize+ /warn:4 ('/out:'+(Join-Path $profile 'Mods/Delve/Delve.dll')) $refs (Get-ChildItem (Join-Path $profile 'CodeSnapshot') -Filter '*.cs' | ForEach-Object FullName)
if($LASTEXITCODE -ne 0){throw 'Frozen core build failed'}
New-Item -ItemType Directory -Path (Join-Path $profile 'Catalogue') -Force|Out-Null
foreach($file in @('src/Forest/catalogue.json','docs/forest-crafting-catalogue.txt','src/Farming/first-pass.json')){Copy-Item -LiteralPath (Join-Path $root $file) -Destination (Join-Path $profile 'Catalogue') -Force}
& $python (Join-Path $PSScriptRoot 'validate_allium_farming.py') --profile $profile
if($LASTEXITCODE -ne 0){throw 'Integrated content validation failed'}
& $python (Join-Path $PSScriptRoot 'validate_farming.py') --mods (Join-Path $profile 'Mods')
if($LASTEXITCODE -ne 0){throw 'Farming validation failed'}
