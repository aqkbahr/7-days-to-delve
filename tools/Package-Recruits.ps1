$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$previous=(Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim()
& (Join-Path $previous 'Verify-Package.ps1')
$release=Join-Path $root ('dist/Delve-Wayrest-Recruits-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $release -Force|Out-Null
Get-ChildItem -LiteralPath $previous | Where-Object Name -notin @('PlaytestData','manifest.json') | ForEach-Object {Copy-Item -LiteralPath $_.FullName -Destination $release -Recurse}
Copy-Item -LiteralPath (Join-Path $root 'src/Delve/Delve.dll') -Destination (Join-Path $release 'Mods/Delve/Delve.dll') -Force
Copy-Item -LiteralPath (Join-Path $root 'src/ZDelveRecruits') -Destination (Join-Path $release 'Mods') -Recurse -Force
Copy-Item -LiteralPath (Join-Path $root 'docs/wayrest-recruits-playtest.txt') -Destination (Join-Path $release 'RECRUITMENT.txt')
Copy-Item -LiteralPath (Join-Path $root 'docs/wayrest-recruits-validation.txt') -Destination (Join-Path $release 'RECRUITMENT-VALIDATION.txt')
$evidence=Join-Path $release 'Evidence/Recruitment';New-Item -ItemType Directory -Path $evidence -Force|Out-Null
foreach($name in @('recruit-results.txt','state-results.txt','recruit-native-definitions.txt','recruit-native-flow.txt')){Copy-Item -LiteralPath (Join-Path $root ('artifacts/tests/'+$name)) -Destination $evidence}
$sourcesPath=Join-Path $release 'sources.json'
if(Test-Path $sourcesPath){$sources=Get-Content $sourcesPath -Raw|ConvertFrom-Json;$sources|Add-Member -NotePropertyName recruitment -NotePropertyValue 'Workspace src/Code/Recruit*.cs and src/ZDelveRecruits; October 25, 2026' -Force;$sources|ConvertTo-Json -Depth 8|Set-Content $sourcesPath -Encoding utf8}
$intro="WAYREST RECRUITMENT UPDATE`r`nRead RECRUITMENT.txt for hiring, station assignment and testing.`r`nThis package has a separate PlaytestData folder; previous saves remain in their original package.`r`nNative fixture and persistence checks pass; human UI/combat and remote multiplayer acceptance remain.`r`n`r`n"
$start=Join-Path $release 'START-HERE.txt';$intro+(Get-Content $start -Raw)|Set-Content $start -Encoding utf8
$manifest=@{name='Allium Wayrest Recruitment Playtest';version='0.8.0-recruits';gameVersion='3.3.0 (b18)';acceptance='Compiled, persistence and native recruitment fixtures checked. Human UI/combat and remote multiplayer acceptance pending.';files=@()}
$manifest.files=@(Get-ChildItem -LiteralPath $release -Recurse -File|Sort-Object FullName|ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$previous|Set-Content (Join-Path $root 'dist/previous-first-forest-release.txt')
$release|Set-Content (Join-Path $root 'dist/latest-first-forest-release.txt')
$release|Set-Content (Join-Path $root 'dist/latest-recruits-release.txt')
Write-Host "Recruitment package: $release"
