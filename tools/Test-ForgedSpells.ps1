$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'artifacts/tests/ForgedSpellTests.exe'
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo ('/out:'+$out) (Join-Path $root 'src/Code/ForgedSpellRules.cs') (Join-Path $root 'src/Code/ProficiencyRules.cs') (Join-Path $root 'tests/ForgedSpellTests.cs')
if($LASTEXITCODE -ne 0){throw 'Forged rule tests did not compile'}
& $out | Tee-Object (Join-Path $root 'artifacts/validation/forged-rules.txt')
if($LASTEXITCODE -ne 0){throw 'Forged rule tests failed'}
