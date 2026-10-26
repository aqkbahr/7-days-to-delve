$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'artifacts/tests'
New-Item -ItemType Directory -Path $out -Force | Out-Null
$compiler=Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
& $compiler /nologo /target:exe ('/out:'+(Join-Path $out 'ProgressionTests.exe')) (Join-Path $root 'src/Code/ProficiencyRules.cs') (Join-Path $root 'src/Code/TalentRules.cs') (Join-Path $root 'src/Code/TalentCatalog.generated.cs') (Join-Path $root 'src/Code/SummonTalents.cs') (Join-Path $root 'tests/ProgressionTests.cs')
if($LASTEXITCODE -ne 0){throw 'Progression test compilation failed'}
& (Join-Path $out 'ProgressionTests.exe') | Out-File (Join-Path $out 'progression-results.txt')
if($LASTEXITCODE -ne 0){throw 'Progression tests failed'}
Get-Content (Join-Path $out 'progression-results.txt') -Tail 1
