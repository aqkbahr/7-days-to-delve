$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'artifacts/tests/Rank20Tests.exe'
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo ('/out:'+$out) (Join-Path $root 'src/Code/Rank20Rules.cs') (Join-Path $root 'tests/Rank20Tests.cs')
if($LASTEXITCODE -ne 0){throw 'Rank-20 tests did not compile'}
& $out | Tee-Object (Join-Path $root 'artifacts/tests/rank20-results.txt')
if($LASTEXITCODE -ne 0){throw 'Rank-20 rules failed'}
