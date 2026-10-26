$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'artifacts/tests/SkillCoverageTests.exe'
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /target:exe ('/out:'+$out) (Join-Path $root 'src/SkillCoverage/CoverageRules.cs') (Join-Path $root 'tests/SkillCoverageTests.cs')
if($LASTEXITCODE -ne 0){throw 'Coverage test compilation failed'}
& $out|Tee-Object (Join-Path $root 'artifacts/validation/skill-coverage/rules.txt')
if($LASTEXITCODE -ne 0){throw 'Coverage tests failed'}
