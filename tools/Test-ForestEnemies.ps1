$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'artifacts/tests'
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /target:exe ('/out:'+(Join-Path $out 'ForestRulesTests.exe')) (Join-Path $root 'src/Forest/ForestRules.cs') (Join-Path $root 'tests/ForestRulesTests.cs')
if($LASTEXITCODE -ne 0){throw 'Forest test compilation failed'}
& (Join-Path $out 'ForestRulesTests.exe') | Tee-Object -FilePath (Join-Path $out 'forest-rules.txt')
if($LASTEXITCODE -ne 0){throw 'Forest rules failed'}
& 'C:/Users/Michael/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' (Join-Path $PSScriptRoot 'validate_forest_enemies.py')
if($LASTEXITCODE -ne 0){throw 'Forest content validation failed'}
