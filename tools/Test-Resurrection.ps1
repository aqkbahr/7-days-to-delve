$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'artifacts/tests'
New-Item -ItemType Directory -Path $out -Force|Out-Null
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /target:exe ('/out:'+(Join-Path $out 'ResurrectionTests.exe')) (Join-Path $root 'src/Code/WorldStateStore.cs') (Join-Path $root 'src/Code/RecruitRecords.cs') (Join-Path $root 'tests/ResurrectionTests.cs')
if($LASTEXITCODE -ne 0){throw 'Resurrection test compilation failed'}
& (Join-Path $out 'ResurrectionTests.exe') $out | Tee-Object -FilePath (Join-Path $out 'resurrection-results.txt')
if($LASTEXITCODE -ne 0){throw 'Resurrection tests failed'}
