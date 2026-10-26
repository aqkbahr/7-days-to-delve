param([string]$ProfileName='ForestTerrain',[switch]$Promote)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root "playtest/$ProfileName"
$evidence=Join-Path $root 'artifacts/validation/forest-terrain'
$base=(Get-Content (Join-Path $profile 'base-release.txt') -Raw).Trim()
$runtime=Get-Content (Join-Path $evidence 'runtime.txt') -Raw
$race=Get-Content (Join-Path $evidence 'race-after.txt') -Raw
$cloneInitial=Get-Content (Join-Path $evidence 'clone-fixed-initial-server.log') -Raw
$cloneReload=Get-Content (Join-Path $evidence 'clone-fixed-reload-server.log') -Raw
$cloneResults=(Get-Content (Join-Path $evidence 'clone-console-transcript.txt') -Raw).Split(@('INITIAL,'),[StringSplitOptions]::None)[1]
if(([regex]::Matches($cloneResults,'\[TerrainClone\] PASS')).Count -lt 2 -or $cloneResults -notmatch '\[TerrainChannels\] PASS' -or $cloneResults -match '\] FAIL\b'){throw 'Sparse clone/channel console regressions required'}
foreach($log in @($cloneInitial,$cloneReload)){
 if($log -notmatch 'Sparse prefab clone guards enabled' -or $log -match '\bEXC\b|DecorateChunkOverlapping|COPY FAILED|\] FAIL\b'){throw 'Sparse-clone initial/reload patch missing or failed'}
}
foreach($dungeon in @('delve_dungeon_cave_06','delve_dungeon_cave_11','delve_dungeon_cemetery_02','delve_dungeon_cave_12')){
 if($cloneInitial -notmatch ('PASS ready '+$dungeon)){throw "Initialized fresh terrain required: $dungeon"}
}
if($runtime+$race -match '\] FAIL|\bEXC\b|Exception:|DecorateChunkOverlapping'){throw 'Final acceptance contains a failure'}
if(([regex]::Matches($race,'PASS 120/120')).Count -lt 3 -or $race -notmatch 'PASS decoder exception preserved'){throw 'Concurrent-load and exception-release regression checks required'}
foreach($pattern in @('\[ForestReady\] PASS 208','\[Processing\] PASS 255','\[Forged\] PASS 210','PASS: 614 loaded','\[Farming\] PASS 240','\[Pantry\] PASS 22','\[PrefabAudit\] PASS 108','\[TerrainAudit\] PASS','PASS native BloodMoon party','PASS native Blood Moon clock','PASS first-night state reload')){
 if($runtime -notmatch $pattern){throw "Missing final acceptance: $pattern"}
}

foreach($dungeon in @('delve_dungeon_cave_06','delve_dungeon_cave_11','delve_dungeon_cemetery_02','delve_dungeon_cave_12')){
 if($runtime -notmatch ('PASS generated '+$dungeon) -or $runtime -notmatch ('PASS guardian '+$dungeon)){throw "Fresh dungeon acceptance missing: $dungeon"}
}
foreach($phase in @('initial','reload')){
 $log=Get-Content (Join-Path $evidence "$phase-server.log") -Raw
 if($log -notmatch '\[DelveTerrain\] Native prefab decoder synchronization enabled' -or $log -match '\bEXC\b|DecorateChunkOverlapping|\[TerrainDiagnostic\] COPY FAILED'){throw "Terrain error or missing patch: $phase"}
}
$modules=@('Delve','DelveWayrest','DelveWildlife','ZDelveDungeons','ZDelveForest')
$snapshot=Get-Content (Join-Path $evidence 'tested-mods.json') -Raw | ConvertFrom-Json
foreach($entry in $snapshot){if((Get-FileHash (Join-Path $profile ('Mods/'+$entry.path))).Hash -ne $entry.sha256){throw "Tested file changed: $($entry.path)"}}
$files=@(foreach($name in $modules){Get-ChildItem (Join-Path $profile "Mods/$name") -Recurse -File})
if($files.Count -ne $snapshot.Count){throw 'Tested production file inventory changed'}
$baseFiles=@(foreach($name in $modules){Get-ChildItem (Join-Path $base "Mods/$name") -Recurse -File})
if($files.Count -ne $baseFiles.Count+1 -or !(Test-Path (Join-Path $profile 'Mods/Delve/DelveTerrainCompatibility.dll'))){throw 'Only the terrain compatibility assembly may be added'}
# This release must preserve the previously tested gameplay and map exactly;
# only the separately compiled decoder compatibility assembly is new.
foreach($name in $modules){foreach($file in Get-ChildItem (Join-Path $base "Mods/$name") -Recurse -File){
 $relative=$file.FullName.Substring($base.Length+1)
 if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash (Join-Path $profile $relative)).Hash){throw "Unexpected gameplay change: $relative"}
}}
$world=Join-Path $base 'Worlds/Allium-v0.10'
foreach($file in Get-ChildItem $world -Recurse -File){
 $relative=$file.FullName.Substring($world.Length+1)
 if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash (Join-Path $profile "GeneratedWorlds/Allium-v0.10/$relative")).Hash){throw "Tested world changed: $relative"}
}
$release=Join-Path $root ('dist/Delve-First-Forest-Clean-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory $release,(Join-Path $release 'Mods'),(Join-Path $release 'Worlds'),(Join-Path $release 'Evidence') | Out-Null
foreach($name in $modules){Copy-Item (Join-Path $profile "Mods/$name") (Join-Path $release 'Mods') -Recurse}
Copy-Item $world (Join-Path $release 'Worlds') -Recurse
Copy-Item (Join-Path $base 'Catalogue') $release -Recurse
foreach($name in @('Play-Allium.cmd','Play-Allium.ps1','Verify-Package.ps1','world-name.txt','dungeons-atlas.png','dungeons.json','locations-atlas.png','locations.json','resource-atlas.png','resource-sites.json')){Copy-Item (Join-Path $base $name) $release}
Copy-Item (Join-Path $root 'docs/forest-ready-playtest.txt') (Join-Path $release 'START-HERE.txt')
Copy-Item (Join-Path $root 'docs/forest-ready-validation.txt') (Join-Path $release 'VALIDATION.txt')
Copy-Item (Join-Path $root 'docs/forest-terrain-fix.txt') (Join-Path $release 'TERRAIN-FIX.txt')
foreach($name in @('runtime.txt','race-after.txt','initial-server.log','reload-server.log','clone-fixed-initial-server.log','clone-fixed-reload-server.log','clone-console-transcript.txt','tested-mods.json','closure.json')){Copy-Item (Join-Path $evidence $name) (Join-Path $release 'Evidence')}
New-Item -ItemType Directory (Join-Path $release 'Evidence/BeforeFix') | Out-Null
Copy-Item (Join-Path $evidence 'race-before-ready.txt') (Join-Path $release 'Evidence/BeforeFix')
Copy-Item (Join-Path $evidence 'clone-before-server.log') (Join-Path $release 'Evidence/BeforeFix')
$manifest=@{name='Delve First Forest Playtest - Terrain Fix';version='0.7.2-playtest';gameVersion='3.3.0 (b18)';baseRelease=(Split-Path $base -Leaf);acceptance='Concurrent prefab decoder and sparse clone regressions, initialized fresh-world terrain and process reload passed; human playtest balance remains';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File | Sort-Object FullName | ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release | Set-Content (Join-Path $root 'dist/latest-terrain-validated.txt')
if($Promote){foreach($name in @('latest-first-forest-release.txt','latest-forest-release.txt','latest-allium-release.txt','latest-release.txt')){$release | Set-Content (Join-Path $root "dist/$name")}}
Write-Host "Clean first Forest playtest: $release"



