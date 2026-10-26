$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$evidence=Join-Path $root 'artifacts/validation/station-progression'
$release=(Get-Content (Join-Path $evidence 'candidate.txt') -Raw).Trim()
$baseline=(Get-Content (Join-Path $evidence 'base.txt') -Raw).Trim()
$selected=Join-Path $root 'dist/latest-first-forest-release.txt'
if((Get-Content $selected -Raw).Trim() -ne $baseline){throw 'The selected baseline changed; reconcile before promotion.'}
$audit=Get-Content (Join-Path $evidence 'audit.json') -Raw|ConvertFrom-Json
if($audit.result -ne 'PASS' -or $audit.later_dependencies.Count){throw 'Dependency audit failed'}
foreach($check in @(@('native-final.txt','\[StationProgression\] PASS \d+ native checks; 237 exact variants, 141 station queue outputs'),@('native-final.txt','PASS: 617'),@('batch04-final.txt','\[Batch04\] PASS'),@('persistence-seed-server.log','\[StationPersistence\] PASS seed 21'),@('persistence-check-server.log','\[StationPersistence\] PASS check 21'))){
 if((Get-Content (Join-Path $evidence $check[0]) -Raw) -notmatch $check[1]){throw ('Missing acceptance: '+$check[0])}
}
& (Join-Path $baseline 'Verify-Package.ps1')
& (Join-Path $release 'Verify-Package.ps1')
$dest=Join-Path $release 'Evidence/StationProgression';New-Item -ItemType Directory $dest -Force|Out-Null
foreach($name in @('audit.json','changes.json','native-final.txt','batch04-final.txt','persistence-seed-server.log','persistence-check-server.log','final-terrain-server.log')){Copy-Item (Join-Path $evidence $name) $dest -Force}
foreach($name in @('StationProgression.cs','Catalog.generated.cs')){Copy-Item (Join-Path $root ('src/ZZZZZZZZZZDelveCraftingStations/'+$name)) $dest -Force}
Copy-Item (Join-Path $root 'docs/station-progression-playtest.txt') (Join-Path $release 'START-HERE.txt') -Force
Copy-Item (Join-Path $root 'docs/station-progression-maintenance.txt') $dest -Force
$null=(Get-Content (Join-Path $evidence 'native-final.txt') -Raw) -match '\[StationProgression\] PASS (\d+)';$nativeCount=$Matches[1]
$validation=@"
CRAFTING SPLIT AND STATION PROGRESSION - 0.11.0
PASS: 237 exact variants: 96 inventory and 141 station variants. 236 are within
proficiency 20; the accepted Alchemy-40 excavation charge remains gated at 40.
PASS: full ingredient/tool/station/water-production closure through proficiency 20;
65 repair bindings; no later-stage dependencies. $($audit.baseline_files_retained) baseline Mods/Worlds files retained.
PASS: $nativeCount native checks, including all recipe gates, all 141 station queue
outputs, all 21 station menus, earlier-tier inclusion and wrong-station exclusion.
PASS: 617 loaded core checks and the Batch 04 storage/rune backend regression.
PASS: all 21 placed stations, stored output and exact queued recipe variants
survive an actual server shutdown/restart; every reloaded queue completes correctly.
Lead byproducts from iron deposits close the early wand-rune supply chain.
The latest POI elevation correction, Skill Coverage, Batch 04 content, UI fixes
and nearby storage remain. Final crafting/backend checks pass in a fresh save
on corrected terrain. Queue persistence used the same gameplay modules on the
prior terrain revision. This release needs a NEW SAVE for the terrain correction.
Tests use an isolated native server, not the user's save. Human menu interaction,
visual acceptance, natural progression balance and remote-client multiplayer
remain playtest checks. See Evidence/StationProgression and CRAFTING-STATIONS.txt.

Historical baseline evidence follows.

"@
$file=Join-Path $release 'VALIDATION.txt';($validation+(Get-Content $file -Raw))|Set-Content $file
$manifestPath=Join-Path $release 'manifest.json';$manifest=Get-Content $manifestPath -Raw|ConvertFrom-Json
$manifest.version='0.11.0-station-progression'
$manifest.files=@(Get-ChildItem $release -Recurse -File|Where-Object {$_.FullName -ne $manifestPath}|Sort-Object FullName|ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest|ConvertTo-Json -Depth 6|Set-Content $manifestPath
& (Join-Path $release 'Verify-Package.ps1')
if((Get-Content $selected -Raw).Trim() -ne $baseline){throw 'Selected package changed during verification; promotion stopped.'}
$baseline|Set-Content (Join-Path $root 'dist/previous-first-forest-release.txt')
$release|Set-Content (Join-Path $root 'dist/latest-station-progression-release.txt')
$release|Set-Content $selected
Write-Host "Selected verified build: $release"

