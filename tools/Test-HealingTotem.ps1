$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$exe=Join-Path $root 'artifacts/tests/HealingTotemTests.exe'
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo ('/out:'+$exe) (Join-Path $root 'src/Code/HealingTotemRules.cs') (Join-Path $root 'tests/HealingTotemTests.cs')
if($LASTEXITCODE -ne 0){throw 'Healing test compile failed'}
& $exe | Tee-Object -FilePath (Join-Path $root 'artifacts/validation/healing-rules.txt')
if($LASTEXITCODE -ne 0){throw 'Healing rules failed'}
