$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'artifacts/tests'
New-Item -ItemType Directory -Path $out -Force|Out-Null
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /target:exe ('/out:'+(Join-Path $out 'RecruitTests.exe')) (Join-Path $root 'src/Code/WorldStateStore.cs') (Join-Path $root 'src/Code/RecruitRecords.cs') (Join-Path $root 'tests/RecruitTests.cs')
if($LASTEXITCODE -ne 0){throw 'Recruit test compilation failed'}
& (Join-Path $out 'RecruitTests.exe') $out | Tee-Object -FilePath (Join-Path $out 'recruit-results.txt')
if($LASTEXITCODE -ne 0){throw 'Recruit tests failed'}
