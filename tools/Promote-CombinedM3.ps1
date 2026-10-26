param([string]$ProfileName='CombinedFinal',[string]$EvidenceName='combined-final')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$candidate=(Get-Content (Join-Path $root 'dist/latest-combined-m3-candidate.txt') -Raw).Trim()
$profile=Join-Path $root ('playtest/'+$ProfileName)
if($EvidenceName -notmatch '^[A-Za-z0-9_-]+$'){throw 'Invalid evidence name'}
$evidence=Join-Path $root ('artifacts/validation/'+$EvidenceName)
$dungeons=Join-Path $root ('artifacts/validation/'+$EvidenceName+'-dungeons')
$validation=Get-Content (Join-Path $root 'docs/combined-m3-validation.txt') -Raw
if($validation -notmatch 'STATUS: AUTOMATED CHECKS PASS' -or $validation -match 'CHECKS PENDING'){throw 'Completed validation record required'}
$expectedMods=@('Delve','DelveWayrest','DelveWildlife','ZDelveDungeons','ZDelveForest')
$actualMods=@(Get-ChildItem (Join-Path $candidate 'Mods') -Directory|ForEach-Object Name)
if(Compare-Object $expectedMods $actualMods){throw 'Unexpected/missing production module or developer harness in candidate'}
foreach($name in @('core','runtime','roster','horde','damage','heavy','timeline','warden','reload','dungeon-ready-reload','dungeon-ceiling-reload')) {
 $text=Get-Content (Join-Path $evidence ($name+'.txt')) -Raw
 if($text -notmatch 'PASS' -or $text -match '\] FAIL'){throw "Acceptance check missing/failed: $name"}
}
foreach($name in @('processing','farming','pantry','healing','closure','decoder-race','decoder-faults','closure-reload','decoder-faults-reload','core-reload','processing-reload','farming-reload','pantry-reload','healing-reload','runtime-reload','forged-reload')){
 $text=Get-Content (Join-Path $evidence ($name+'.txt')) -Raw
 if($text -notmatch 'PASS' -or $text -match '(\] FAIL|HEALING FAIL|FAIL:)'){throw "M3 acceptance missing/failed: $name"}
}
$roster=@('delveCorruptedWalker','delveImp','delvePossessedSoldier','delveDemonSpawn','delveHellhound','delveWarpedBrute','delveAshboundWarden','delveThornbackBoar','delveGloomcat','delveCrystalStag')
foreach($name in @('sparse-clone','sparse-clone-reload')){
 $text=Get-Content (Join-Path $evidence ($name+'.txt')) -Raw
 if($text -notmatch '\[TerrainClone\] PASS' -or $text -match '\[TerrainClone\] FAIL'){throw "Sparse clone regression missing/failed: $name"}
}
foreach($name in @('sparse-channels','sparse-channels-reload')){
 $text=Get-Content (Join-Path $evidence ($name+'.txt')) -Raw
 if($text -notmatch '\[TerrainChannels\] PASS' -or $text -match '\[TerrainChannels\] FAIL'){throw "Sparse channel regression missing/failed: $name"}
}
foreach($enemy in $roster){
 $text=Get-Content (Join-Path $evidence ('forged-'+$enemy+'.txt')) -Raw
 if($text -notmatch '\[Forged\] PASS' -or $text -match '\[Forged\] FAIL'){throw "Spell interaction failed: $enemy"}
}
$poiText=Get-Content (Join-Path $evidence 'pois.txt') -Raw
if(([regex]::Matches($poiText,'\[Integrated\] PASS POI')).Count -ne 15 -or $poiText -match '\] FAIL'){throw 'Fifteen POI checks required'}
$dungeonChecks=@('flora','registry','board','ceiling-generated','ceiling-regression','smuggler-after-reset-stress')
foreach($index in 0..3){foreach($phase in @('ready','carving','floor-stress','reset','ready-after-reset','after-reset','guardian')){$dungeonChecks+="$phase-$index"}}
foreach($name in $dungeonChecks) {
 $text=Get-Content (Join-Path $dungeons ($name+'.txt')) -Raw
 if($text -notmatch '\[Dungeons\] PASS' -or $text -match '\[Dungeons\] FAIL'){throw "Dungeon acceptance missing/failed: $name"}
}
$report=Get-Content (Join-Path $evidence 'content.json') -Raw|ConvertFrom-Json
if($report.result -ne 'PASS' -or $report.mods.Count -ne 5){throw 'Combined static validation required'}
$snapshot=Get-Content (Join-Path $evidence 'tested-mods.json') -Raw|ConvertFrom-Json
foreach($logName in @('initial-server.log','reload-server.log')){
 $log=Get-Content (Join-Path $evidence $logName) -Raw
 if($log -notmatch 'StartGame done' -or $log -match 'NullReferenceException|IndexOutOfRangeException|ArgumentOutOfRangeException|\[TerrainDiagnostic\] COPY FAILED|\bERR\s+.*(XML|Harmony|[Bb]lock|[Pp]refab)'){throw "Content/terrain exception in acceptance log: $logName"}
}
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
Copy-Item -LiteralPath (Join-Path $root 'docs/combined-m3-playtest.txt') -Destination (Join-Path $release 'START-HERE.txt')
Copy-Item -LiteralPath (Join-Path $root 'docs/combined-m3-validation.txt') -Destination (Join-Path $release 'VALIDATION.txt')
Copy-Item -LiteralPath (Join-Path $root 'docs/forest-first-playthrough.txt') -Destination (Join-Path $release 'FIRST-PLAYTHROUGH.txt')
Copy-Item -LiteralPath (Join-Path $root 'docs/combined-terrain-fix.txt') -Destination (Join-Path $release 'TERRAIN-FIX.txt')
Copy-Item (Join-Path $root 'dist/Delve-Forest-M3-20261024-220158/PROCESSING-GUIDE.txt') $release
foreach($name in @('M3-EQUIPMENT-SPELLS.txt','M3-PLAYTEST.txt','PROCESSING-GUIDE.txt')){
 $path=Join-Path $release $name
 (Get-Content $path -Raw).Replace('Allium-v0.9','Allium-v0.10').Replace('Catalogue/forged.json','Catalogue/forest-ready-catalogue.txt').Replace('Worlds/Allium-v0.10/resource-sites.json','resource-sites.json')|Set-Content $path -Encoding utf8
}
$processingGuide=Join-Path $release 'PROCESSING-GUIDE.txt'
$processingText=Get-Content $processingGuide -Raw
$processingText=$processingText.Replace('Catalogue/processing.json lists all 44 new recipe variants with exact inputs,','Catalogue/forest-ready-catalogue.txt lists enabled recipes with exact inputs,')
$processingText=$processingText.Replace('processing with remaining planned M3 equipment/runes/protection.','processing with the included M3 equipment, runes and protection supplies.')
$processingText | Set-Content $processingGuide -Encoding utf8
$m3Checklist=Join-Path $release 'M3-PLAYTEST.txt'
((Get-Content $m3Checklist -Raw) -replace '(?s)This package uses the verified v0\.9 map\..*?not included in this release\.','This combined package includes the Allium-v0.10 delves, revised Forest enemies and first-horde behavior, M3 equipment/spells and the current crafting closure. See VALIDATION.txt for final native acceptance and remaining human checks.') | Set-Content $m3Checklist -Encoding utf8
$craftingGuide=Join-Path $release 'CRAFTING-GUIDE.txt'
(Get-Content $craftingGuide -Raw).Replace('The native prefab-decoder race behind the earlier terrain-decoration error is','The native prefab-decoder race and sparse-clone terrain-decoration defects are').Replace('fixed in version 0.7.1.','fixed in version 0.7.2.') | Set-Content $craftingGuide -Encoding utf8
Copy-Item -LiteralPath $evidence -Destination (Join-Path $release 'Evidence/CombinedM3Acceptance') -Recurse
Copy-Item -LiteralPath $dungeons -Destination (Join-Path $release 'Evidence/CombinedM3Dungeons') -Recurse
$harnessEvidence=Join-Path $release 'Evidence/CombinedTestHarness'
New-Item -ItemType Directory $harnessEvidence -Force | Out-Null
foreach($source in @('tools/allium/DungeonVerify.cs','tools/allium/ForgedProbe.cs','tools/forest/TerrainDiagnostic.cs','tools/Test-CombinedM3.ps1','tools/Test-Dungeons.ps1')){
 Copy-Item (Join-Path $root $source) $harnessEvidence
}
foreach($name in @('combined-latest-items-audit.txt','combined-latest-progression-semantic-diff.json','combined-latest-independent-audit.txt')){
 Copy-Item (Join-Path $root ('artifacts/validation/'+$name)) (Join-Path $release 'Evidence')
}
$sources=Get-Content (Join-Path $release 'sources.json') -Raw|ConvertFrom-Json
$sources.engineValidation='PASS: combined native-engine fixtures; human playthrough and multiplayer not validated'
$sources.spellCompatibility='PASS: native entity-root/model collider ownership; splash and solid-wall regressions across all ten Allium creatures, plus process reload'
$sources.terrainCompatibility.acceptance='PASS: concurrent decoder, exception release, poisoned sparse clone and all five channel defaults, expanded native generation, and process reload'
$sources|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'sources.json') -Encoding utf8
$manifest=@{name='Allium Combined First Playtest';version='0.7.2-playtest';gameVersion='3.3.0 (b18)';acceptance='Native-engine validated; human gameplay acceptance remains';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File|Where-Object {$_.FullName -ne (Join-Path $release 'manifest.json')}|Sort-Object FullName|ForEach-Object{@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
foreach($pointer in @('latest-integrated-release.txt','latest-allium-release.txt','latest-allium-progression-release.txt','latest-forest-bestiary-release.txt','latest-forest-release.txt','latest-first-forest-release.txt','latest-release.txt')){$release|Set-Content (Join-Path $root ('dist/'+$pointer)) -Encoding utf8}
Write-Host "Combined solo playtest: $release"

