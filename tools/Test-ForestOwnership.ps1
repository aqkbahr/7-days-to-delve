$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'artifacts/tests/ForestOwnershipTests.exe'
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo ('/out:'+$out) (Join-Path $root 'src/Code/ForestRecipeOwnership.generated.cs') (Join-Path $root 'tests/ForestOwnershipTests.cs')
if($LASTEXITCODE -ne 0){throw 'Ownership compile failed'}
& $out
if($LASTEXITCODE -ne 0){throw 'Ownership tests failed'}
