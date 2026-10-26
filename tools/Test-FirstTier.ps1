$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'artifacts/tests'
New-Item -ItemType Directory -Path $out -Force | Out-Null
$sources=@('src/Code/FirstTierRules.cs','src/Code/ProficiencyRules.cs','src/Code/TalentRules.cs','src/Code/TalentCatalog.generated.cs','src/Code/SummonTalents.cs','tests/FirstTierTests.cs') | ForEach-Object {Join-Path $root $_}
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /target:exe ('/out:'+(Join-Path $out 'FirstTierTests.exe')) $sources
if($LASTEXITCODE -ne 0){throw 'First-tier test compilation failed'}
& (Join-Path $out 'FirstTierTests.exe') | Tee-Object -FilePath (Join-Path $out 'first-tier-results.txt')
if($LASTEXITCODE -ne 0){throw 'First-tier tests failed'}
