param([string]$ProfileName='ForestUnifiedM3')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root "playtest/$ProfileName"
$evidence=Join-Path $root 'artifacts/validation/forest-unified-m3'
$sources=Get-Content (Join-Path $profile 'sources.json') -Raw | ConvertFrom-Json
$required=@('core','forged','processing','farming','pantry','healing','registry','runtime','roster','damage','heavy','horde','timeline','warden','board','ceiling-regression','smuggler-after-reset-stress','reload-core','reload-forged','reload-processing','reload-runtime','reload','reload-registry')
foreach($i in 0..3){foreach($phase in @('carving','floor-stress','reset','after-reset','guardian')){$required+="$phase-$i"}}
foreach($i in 0..14){$required+="poi-$i"}
$required+='ceiling-generated'
$required+='prefab-audit'
$required+='hellhound-fix-initial'
$required+='brute-fix-initial'
foreach($enemy in @('delveCorruptedWalker','delveImp','delvePossessedSoldier','delveDemonSpawn','delveHellhound','delveWarpedBrute')){$required+="spell-$enemy"}
foreach($name in $required){
 $result=Get-Content (Join-Path $evidence "$name.txt") -Raw
 if($result -notmatch 'PASS' -or $result -match '\] FAIL|HEALING FAIL|Exception'){throw "Missing or failed acceptance: $name"}
}
foreach($name in @('content','catalogue')){if((Get-Content (Join-Path $evidence "$name.json") -Raw | ConvertFrom-Json).result -ne 'PASS'){throw "Static validation failed: $name"}}
$modules=@('Delve','DelveWayrest','DelveWildlife','ZDelveDungeons','ZDelveForest')
$snapshot=Get-Content (Join-Path $evidence 'tested-mods.json') -Raw | ConvertFrom-Json
foreach($entry in $snapshot){if((Get-FileHash (Join-Path $profile ('Mods/'+$entry.path))).Hash -ne $entry.sha256){throw "Tested file changed: $($entry.path)"}}
$files=@(foreach($name in $modules){Get-ChildItem (Join-Path $profile "Mods/$name") -Recurse -File})
if($files.Count -ne $snapshot.Count){throw 'Production inventory differs from tested snapshot'}
$world=Join-Path $sources.candidate 'Worlds/Allium-v0.10'
foreach($file in Get-ChildItem $world -Recurse -File){
 $relative=$file.FullName.Substring($world.Length+1)
 if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash (Join-Path $profile "GeneratedWorlds/Allium-v0.10/$relative")).Hash){throw "Tested world changed: $relative"}
}
$release=Join-Path $root ('dist/Delve-Unified-M3-v0.10-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory $release,(Join-Path $release 'Mods'),(Join-Path $release 'Worlds'),(Join-Path $release 'Evidence') | Out-Null
foreach($name in $modules){Copy-Item (Join-Path $profile "Mods/$name") (Join-Path $release 'Mods') -Recurse}
Copy-Item $world (Join-Path $release 'Worlds') -Recurse
Copy-Item (Join-Path $sources.core 'Catalogue') $release -Recurse
Copy-Item $evidence (Join-Path $release 'Evidence/UnifiedAcceptance') -Recurse
foreach($name in @('Play-Allium.cmd','Play-Allium.ps1','Verify-Package.ps1')){Copy-Item (Join-Path $PSScriptRoot "package/$name") $release}
foreach($name in @('dungeons-atlas.png','dungeons.json','locations-atlas.png','locations.json','resource-atlas.png','resource-sites.json')){Copy-Item (Join-Path $sources.candidate $name) $release}
'Allium-v0.10' | Set-Content (Join-Path $release 'world-name.txt')
Copy-Item (Join-Path $root 'docs/forest-unified-playtest.txt') (Join-Path $release 'START-HERE.txt')
Copy-Item (Join-Path $root 'docs/forest-unified-validation.txt') (Join-Path $release 'VALIDATION.txt')
Copy-Item (Join-Path $root 'docs/forest-first-playthrough.txt') (Join-Path $release 'FIRST-PLAYTHROUGH.txt')
Copy-Item (Join-Path $root 'docs/forest-unified-equipment-checklist.txt') (Join-Path $release 'EQUIPMENT-CHECKLIST.txt')
Copy-Item (Join-Path $sources.core 'START-HERE.txt') (Join-Path $release 'FORGED.txt')
Copy-Item (Join-Path $sources.core 'PROCESSING-GUIDE.txt') (Join-Path $release 'PROCESSING.txt')
Copy-Item (Join-Path $root 'docs/forest-unified-dungeons.txt') (Join-Path $release 'DUNGEONS.txt')
# Inherited mechanic guides must identify this package's world consistently.
foreach($name in @('FORGED.txt','PROCESSING.txt')){ $path=Join-Path $release $name; (Get-Content $path -Raw).Replace('Allium-v0.9','Allium-v0.10') | Set-Content $path }
$processing=Join-Path $release 'PROCESSING.txt'
(Get-Content $processing -Raw).Replace('remaining planned M3 equipment/runes/protection','implemented M3 equipment/runes and planned Arbor protection') | Set-Content $processing
$sources | ConvertTo-Json | Set-Content (Join-Path $release 'sources.json')
$manifest=@{name='Delve Unified Forest M3 and v0.10';version='0.6.1-dev';gameVersion='3.3.0 (b18)';acceptance='Combined native-engine initial/reload checks pass; human gameplay acceptance remains';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File | Sort-Object FullName | ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
foreach($name in @('latest-integrated-release.txt','latest-forest-release.txt','latest-allium-release.txt','latest-forest-bestiary-release.txt','latest-release.txt')){$release | Set-Content (Join-Path $root "dist/$name")}
Write-Host "Unified playtest package: $release"
