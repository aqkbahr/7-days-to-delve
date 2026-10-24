$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'artifacts/tests'
New-Item -ItemType Directory -Path $out -Force | Out-Null
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /target:exe ('/out:'+(Join-Path $out 'IncursionRulesTests.exe')) (Join-Path $root 'src/Code/IncursionRules.cs') (Join-Path $root 'tests/IncursionRulesTests.cs')
if($LASTEXITCODE -ne 0) { throw 'Incursion test compilation failed' }
& "$out/IncursionRulesTests.exe" | Tee-Object -FilePath "$out/incursion-results.txt"
if($LASTEXITCODE -ne 0) { throw 'Incursion rules failed' }
