param([ValidateSet('Allium-v0.2','Allium-v0.3','Allium-v0.4','Allium-v0.5','Allium-v0.6','Allium-v0.7','Allium-v0.8','Allium-v0.9','Allium-v0.10')][string]$WorldName='Allium-v0.5',[string]$ProfileName='WayrestCampaignFinal',[string]$BaseDelveRelease='')
$ErrorActionPreference='Stop'
if($WorldName -eq 'Allium-v0.10') {
    $elevationReceipt=Join-Path (Split-Path $PSScriptRoot -Parent) 'artifacts/maps/Allium-v0.10/poi-elevation.json'
    if(!(Test-Path $elevationReceipt)){throw 'Apply tools/fix_allium_poi_elevation.py to the raw world before native validation and packaging; uncorrected POI elevations must not ship.'}
}
$root=Split-Path $PSScriptRoot -Parent
$world=Join-Path $root ('artifacts/maps/'+$WorldName)
$metadata=Join-Path $root ("playtest/$ProfileName/GeneratedWorlds/$WorldName/main.ttw")
if (!(Test-Path $metadata)) { throw 'Run the isolated Allium harness first to generate fresh native metadata.' }
if (!(Test-Path (Join-Path $world 'input-validation.json'))) { throw 'Run validate_allium_world.py first.' }
if ((Get-Content (Join-Path $world 'input-validation.json') -Raw | ConvertFrom-Json).result -ne 'PASS') { throw 'Map input validation did not pass.' }
$release=Join-Path $root ('dist/Delve-'+$WorldName+'-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path (Join-Path $release 'Mods'),(Join-Path $release ('Worlds/'+$WorldName)) -Force | Out-Null
$delveSource=if($BaseDelveRelease){Join-Path (Resolve-Path -LiteralPath $BaseDelveRelease).Path 'Mods/Delve'}else{Join-Path $root 'src/Delve'}
Copy-Item $delveSource (Join-Path $release 'Mods') -Recurse
foreach($file in Get-ChildItem $delveSource -Recurse -File) {
    $relative=$file.FullName.Substring($delveSource.Length+1)
    if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash (Join-Path $root "playtest/$ProfileName/Mods/Delve/$relative")).Hash) { throw "Delve content differs from runtime profile: $relative" }
}
if($WorldName -in @('Allium-v0.4','Allium-v0.5','Allium-v0.6','Allium-v0.7','Allium-v0.8','Allium-v0.9','Allium-v0.10')) {
    Copy-Item (Join-Path $root 'src/DelveWayrest') (Join-Path $release 'Mods') -Recurse
    foreach($file in Get-ChildItem (Join-Path $root 'src/DelveWayrest') -Recurse -File) {
        $relative=$file.FullName.Substring((Join-Path $root 'src/DelveWayrest').Length+1)
        if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash (Join-Path $root "playtest/$ProfileName/Mods/DelveWayrest/$relative")).Hash) { throw "Wayrest content differs from runtime profile: $relative" }
    }
}
$extraModSources=@()
if($BaseDelveRelease){$extraModSources+=@(Get-ChildItem (Join-Path (Resolve-Path -LiteralPath $BaseDelveRelease).Path 'Mods') -Directory | Where-Object Name -notin @('Delve','DelveWayrest','DelveWildlife','ZDelveDungeons') | ForEach-Object FullName)}
if($WorldName -eq 'Allium-v0.10'){$extraModSources+=(Join-Path $root 'src/ZDelveDungeons')}
foreach($extraSource in $extraModSources){
    $extraName=Split-Path $extraSource -Leaf
    foreach($file in Get-ChildItem $extraSource -File -Recurse){
        $relative=$file.FullName.Substring($extraSource.Length+1)
        if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash (Join-Path $root "playtest/$ProfileName/Mods/$extraName/$relative")).Hash){throw "Additional mod differs from runtime: $extraName/$relative"}
    }
    Copy-Item $extraSource (Join-Path $release 'Mods') -Recurse
}
$names=@('dtm.raw','biomes.png','splat1.png','splat2.png','splat3.png','splat4.png','radiation.png','map_info.xml','spawnpoints.xml','prefabs.xml','water_info.xml')
if(Test-Path (Join-Path $world 'poi-elevation.json')){$names+='poi-elevation.json'}
if(Test-Path (Join-Path $root 'src/DelveWildlife')) {
    Copy-Item (Join-Path $root 'src/DelveWildlife') (Join-Path $release 'Mods') -Recurse
    foreach($file in Get-ChildItem (Join-Path $root 'src/DelveWildlife') -Recurse -File) {
        $relative=$file.FullName.Substring((Join-Path $root 'src/DelveWildlife').Length+1)
        if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash (Join-Path $root "playtest/$ProfileName/Mods/DelveWildlife/$relative")).Hash) { throw "Wildlife content differs from runtime profile: $relative" }
    }
    Copy-Item (Join-Path $root 'docs/wildlife-spawns.txt') (Join-Path $release 'WILDLIFE.txt')
}
foreach($name in $names) {
    $tested=Join-Path (Split-Path $metadata) $name
    if((Get-FileHash $tested).Hash -ne (Get-FileHash (Join-Path $world $name)).Hash) { throw "Map input differs from tested profile: $name" }
}
foreach($name in $names) { Copy-Item (Join-Path $world $name) (Join-Path $release ('Worlds/'+$WorldName)) }
Copy-Item $metadata (Join-Path $release ('Worlds/'+$WorldName+'/main.ttw'))
$WorldName | Set-Content (Join-Path $release 'world-name.txt')
foreach($name in @('locations-atlas.png','wayrest-plan.png','locations.json','input-validation.json')) { if(Test-Path (Join-Path $world $name)) { Copy-Item (Join-Path $world $name) $release } }
foreach($name in @('Play-Allium.cmd','Play-Allium.ps1','Verify-Package.ps1')) { Copy-Item (Join-Path $PSScriptRoot "package/$name") $release }
$guide=if($WorldName -eq 'Allium-v0.10') {'forest-delves-playtest.txt'} elseif($WorldName -eq 'Allium-v0.8') {'arbor-playtest.txt'} elseif($WorldName -eq 'Allium-v0.7') {'resources-playtest.txt'} elseif($WorldName -eq 'Allium-v0.6') {'forest-art-playtest.txt'} elseif($WorldName -eq 'Allium-v0.5') {'wayrest-campaign-playtest.txt'} elseif($WorldName -eq 'Allium-v0.4') {'wayrest-playtest.txt'} elseif($WorldName -eq 'Allium-v0.3') {'allium-locations-playtest.txt'} else {'allium-playtest.txt'}
$validation=if($WorldName -eq 'Allium-v0.10') {'forest-delves-validation.txt'} elseif($WorldName -eq 'Allium-v0.8') {'arbor-validation.txt'} elseif($WorldName -eq 'Allium-v0.7') {'resources-validation.txt'} elseif($WorldName -eq 'Allium-v0.6') {'forest-art-validation.txt'} elseif($WorldName -eq 'Allium-v0.5') {'wayrest-campaign-validation.txt'} elseif($WorldName -eq 'Allium-v0.4') {'wayrest-validation.txt'} elseif($WorldName -eq 'Allium-v0.3') {'allium-locations-validation.txt'} else {'allium-runtime-validation.txt'}
if($WorldName -in @('Allium-v0.7','Allium-v0.8','Allium-v0.9','Allium-v0.10')) {
    foreach($name in @('resource-sites.json','resource-atlas.png','ore-build-report.xml')) { Copy-Item (Join-Path $world $name) $release }
    Copy-Item (Join-Path $root 'docs/forest-art-playtest.txt') (Join-Path $release 'FOREST-CAMPAIGN.txt')
}
if($WorldName -in @('Allium-v0.8','Allium-v0.10')) {
    foreach($name in @('arbor-catalog.json','arbor-build.json','arbor-art-report.xml')) { Copy-Item (Join-Path $world $name) $release }
}
if($WorldName -eq 'Allium-v0.6') { Copy-Item (Join-Path $world 'forest-art-report.xml') $release }
if($WorldName -eq 'Allium-v0.10') {
    foreach($name in @('dungeons.json','dungeons-atlas.png','dungeon-art-report.xml')){Copy-Item (Join-Path $world $name) $release}
    if(Test-Path (Join-Path $world 'old-warden-supports.xml')){Copy-Item (Join-Path $world 'old-warden-supports.xml') $release}
    if(Test-Path (Join-Path $world 'dungeon-runtime-validation.json')){Copy-Item (Join-Path $world 'dungeon-runtime-validation.json') $release}
}
Copy-Item (Join-Path $root ('docs/'+$guide)) (Join-Path $release 'START-HERE.txt')
Copy-Item (Join-Path $root ('docs/'+$validation)) (Join-Path $release 'VALIDATION.txt')
$manifest=@{name='7 Days to Delve - Allium exploration alpha';version=$WorldName;gameVersion='3.3.0 (b18)';files=@()}
if($BaseDelveRelease) { $manifest.baseDelveRelease=Split-Path (Resolve-Path -LiteralPath $BaseDelveRelease).Path -Leaf }
$manifest.files=@(Get-ChildItem $release -Recurse -File | Sort-Object FullName | ForEach-Object { @{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash} })
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release | Set-Content (Join-Path $root 'dist/latest-allium-release.txt') -Encoding utf8
Write-Host "Allium package: $release"

