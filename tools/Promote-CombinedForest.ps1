param([string]$ProfileName='ForestCombinedFinal')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$candidate=(Get-Content (Join-Path $root 'dist/latest-combined-candidate.txt') -Raw).Trim()
$profile=Join-Path $root ('playtest/'+$ProfileName)
$evidence=Join-Path $root 'artifacts/validation/forest-combined10'
$dungeons=Join-Path $root 'artifacts/validation/forest-combined-final-dungeons'
$validation=Get-Content (Join-Path $root 'docs/forest-combined-validation.txt') -Raw
if($validation -notmatch 'STATUS: AUTOMATED CHECKS PASS' -or $validation -match 'CHECKS PENDING'){throw 'Completed validation record required'}
$expectedMods=@('Delve','DelveWayrest','DelveWildlife','ZDelveDungeons','ZDelveForest')
$actualMods=@(Get-ChildItem (Join-Path $candidate 'Mods') -Directory|ForEach-Object Name)
if(Compare-Object $expectedMods $actualMods){throw 'Unexpected/missing production module or developer harness in candidate'}
foreach($name in @('core','runtime','roster','horde','damage','heavy','timeline','warden','reload')) {
 $text=Get-Content (Join-Path $evidence ($name+'.txt')) -Raw
 if($text -notmatch 'PASS' -or $text -match '\] FAIL'){throw "Acceptance check missing/failed: $name"}
}
$poiText=Get-Content (Join-Path $evidence 'pois.txt') -Raw
if(([regex]::Matches($poiText,'\[Integrated\] PASS POI')).Count -ne 15 -or $poiText -match '\] FAIL'){throw 'Fifteen POI checks required'}
$dungeonChecks=@('registry','board','ceiling-generated','ceiling-regression','smuggler-after-reset-stress')
foreach($index in 0..3){foreach($phase in @('carving','floor-stress','reset','after-reset','guardian')){$dungeonChecks+="$phase-$index"}}
foreach($name in $dungeonChecks) {
 $text=Get-Content (Join-Path $dungeons ($name+'.txt')) -Raw
 if($text -notmatch '\[Dungeons\] PASS' -or $text -match '\[Dungeons\] FAIL'){throw "Dungeon acceptance missing/failed: $name"}
}
$report=Get-Content (Join-Path $evidence 'content.json') -Raw|ConvertFrom-Json
if($report.result -ne 'PASS' -or $report.mods.Count -ne 5){throw 'Combined static validation required'}
$snapshot=Get-Content (Join-Path $evidence 'tested-mods.json') -Raw|ConvertFrom-Json
$candidateMods=Join-Path $candidate 'Mods'
$actualPaths=@(Get-ChildItem $candidateMods -Recurse -File|ForEach-Object {$_.FullName.Substring($candidateMods.Length+1).Replace('\','/')})
if(Compare-Object @($snapshot|ForEach-Object path) $actualPaths){throw 'Production file set differs from tested snapshot'}
foreach($entry in $snapshot) {
 foreach($folder in @($candidate,$profile)) {
  if((Get-FileHash (Join-Path $folder ('Mods/'+$entry.path))).Hash -ne $entry.sha256){throw "Tested content changed: $($entry.path)"}
 }
}
& (Join-Path $candidate 'Verify-Package.ps1')
$release=Join-Path $root ('dist/Delve-Combined-Playtest-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
Copy-Item -LiteralPath $candidate -Destination $release -Recurse
Copy-Item -LiteralPath (Join-Path $root 'docs/forest-combined-playtest.txt') -Destination (Join-Path $release 'START-HERE.txt')
Copy-Item -LiteralPath (Join-Path $root 'docs/forest-combined-validation.txt') -Destination (Join-Path $release 'VALIDATION.txt')
Copy-Item -LiteralPath (Join-Path $root 'docs/forest-first-playthrough.txt') -Destination (Join-Path $release 'FIRST-PLAYTHROUGH.txt')
Copy-Item -LiteralPath $evidence -Destination (Join-Path $release 'Evidence/CombinedAcceptance') -Recurse
Copy-Item -LiteralPath $dungeons -Destination (Join-Path $release 'Evidence/CombinedDungeons') -Recurse
$sources=Get-Content (Join-Path $release 'sources.json') -Raw|ConvertFrom-Json
$sources.engineValidation='PASS: combined native-engine fixtures; human playthrough and multiplayer not validated'
$sources|ConvertTo-Json|Set-Content (Join-Path $release 'sources.json') -Encoding utf8
$manifest=@{name='Allium Combined Solo Playtest';version='0.5.1-dev-enemies';gameVersion='3.3.0 (b18)';acceptance='Native-engine validated; human gameplay acceptance remains';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File|Where-Object {$_.FullName -ne (Join-Path $release 'manifest.json')}|Sort-Object FullName|ForEach-Object{@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
foreach($pointer in @('latest-integrated-release.txt','latest-allium-release.txt','latest-forest-bestiary-release.txt','latest-release.txt')){$release|Set-Content (Join-Path $root ('dist/'+$pointer)) -Encoding utf8}
Write-Host "Combined solo playtest: $release"
