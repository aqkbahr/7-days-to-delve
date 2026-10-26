$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'artifacts/tests'
New-Item -ItemType Directory -Path $out -Force | Out-Null
$sources=@('src/Code/ProficiencyRules.cs','src/Code/TalentRules.cs','src/Code/TalentCatalog.generated.cs','src/Code/SummonTalents.cs','src/Code/ProgressionUiModel.cs','src/Code/ProgressionUiData.generated.cs','tests/ProgressionUiTests.cs') | ForEach-Object { Join-Path $root $_ }
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /target:exe ('/out:'+(Join-Path $out 'ProgressionUiTests.exe')) $sources
if($LASTEXITCODE -ne 0){throw 'UI test compilation failed'}
& (Join-Path $out 'ProgressionUiTests.exe') | Tee-Object -FilePath (Join-Path $out 'progression-ui-results.txt')
if($LASTEXITCODE -ne 0){throw 'UI model tests failed'}
