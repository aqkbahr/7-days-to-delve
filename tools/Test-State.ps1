$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'artifacts/tests'
New-Item -ItemType Directory -Path $out -Force | Out-Null
$compiler=Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
& $compiler /nologo /target:exe ('/out:'+(Join-Path $out 'WorldStateTests.exe')) (Join-Path $root 'src/Code/WorldStateStore.cs') (Join-Path $root 'src/Code/RecruitRecords.cs') (Join-Path $root 'src/Code/ProficiencyRules.cs') (Join-Path $root 'tests/WorldStateTests.cs')
if($LASTEXITCODE -ne 0){ throw 'State test compilation failed.' }
& (Join-Path $out 'WorldStateTests.exe') $out | Tee-Object -FilePath (Join-Path $out 'state-results.txt')
if($LASTEXITCODE -ne 0){ throw 'State tests failed.' }

