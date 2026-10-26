param([string]$ProfileName='ForestReady')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root "playtest/$ProfileName"
$evidence=Join-Path $root 'artifacts/validation/forest-ready'
$runtime=Get-Content (Join-Path $evidence 'runtime.txt') -Raw
if($runtime -match '\] FAIL|HEALING FAIL|Exception'){throw 'Native runtime acceptance contains a failure; terrain exceptions are no longer exempt'}
if((Get-Content (Join-Path $evidence 'decoration-regression.json') -Raw | ConvertFrom-Json).result -ne 'PASS'){throw 'Decoration regression evidence required'}
foreach($pattern in @('\[ForestReady\] PASS 208','\[Processing\] PASS','\[Forged\] PASS','PASS: 614 loaded')){
 if(([regex]::Matches($runtime,$pattern)).Count -lt 2){throw "Initial and process-reload acceptance required: $pattern"}
}
foreach($pattern in @('\[Farming\] PASS','\[Pantry\] PASS 22','PASS native BloodMoon party','PASS native Blood Moon clock','PASS first-night state reload','\[Incursion\] PASS','\[Dungeons\] PASS registry')){
 if($runtime -notmatch $pattern){throw "Missing native acceptance: $pattern"}
}
foreach($name in @('closure','content')){
 if((Get-Content (Join-Path $evidence "$name.json") -Raw | ConvertFrom-Json).result -ne 'PASS'){throw "Failed static acceptance: $name"}
}
$modules=@('Delve','DelveWayrest','DelveWildlife','ZDelveDungeons','ZDelveForest')
$snapshot=Get-Content (Join-Path $evidence 'tested-mods.json') -Raw | ConvertFrom-Json
foreach($entry in $snapshot){
 if((Get-FileHash (Join-Path $profile ('Mods/'+$entry.path))).Hash -ne $entry.sha256){throw "Tested file changed: $($entry.path)"}
}
$files=@(foreach($name in $modules){Get-ChildItem (Join-Path $profile "Mods/$name") -Recurse -File})
if($files.Count -ne $snapshot.Count){throw 'Tested production file inventory changed'}
$base=(Get-Content (Join-Path $profile 'base-release.txt') -Raw).Trim()
$world=Join-Path $base 'Worlds/Allium-v0.10'
foreach($file in Get-ChildItem $world -Recurse -File){
 $relative=$file.FullName.Substring($world.Length+1)
 if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash (Join-Path $profile "GeneratedWorlds/Allium-v0.10/$relative")).Hash){throw "Tested world changed: $relative"}
}
$release=Join-Path $root ('dist/Delve-First-Forest-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory $release,(Join-Path $release 'Mods'),(Join-Path $release 'Worlds'),(Join-Path $release 'Catalogue'),(Join-Path $release 'Evidence') | Out-Null
foreach($name in $modules){Copy-Item (Join-Path $profile "Mods/$name") (Join-Path $release 'Mods') -Recurse}
Copy-Item $world (Join-Path $release 'Worlds') -Recurse
foreach($name in @('Play-Allium.cmd','Play-Allium.ps1','Verify-Package.ps1')){Copy-Item (Join-Path $PSScriptRoot "package/$name") $release}
foreach($name in @('dungeons-atlas.png','dungeons.json','locations-atlas.png','locations.json','resource-atlas.png','resource-sites.json')){Copy-Item (Join-Path $base $name) $release}
'Allium-v0.10' | Set-Content (Join-Path $release 'world-name.txt')
Copy-Item (Join-Path $root 'docs/forest-ready-playtest.txt') (Join-Path $release 'START-HERE.txt')
Copy-Item (Join-Path $root 'docs/forest-ready-validation.txt') (Join-Path $release 'VALIDATION.txt')
Copy-Item (Join-Path $root 'docs/forest-ready-catalogue.txt') (Join-Path $release 'Catalogue')
Copy-Item (Join-Path $root 'src/Forest/first-playtest.json') (Join-Path $release 'Catalogue')
foreach($name in @('runtime.txt','closure.json','content.json','tested-mods.json','slice-checks.xml','initial-server.log','reload-server.log','decoration-regression.json','decoration-regression.txt','decoration-diagnostic.txt','placed-prefab-audit.txt')){Copy-Item (Join-Path $evidence $name) (Join-Path $release 'Evidence')}
$manifest=@{name='Delve First Forest Playtest';version='0.7.0-playtest';gameVersion='3.3.0 (b18)';baseRelease=(Split-Path $base -Leaf);acceptance='Forest crafting closure and native initial/reload checks pass; human gameplay balance remains to be tested';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File | Sort-Object FullName | ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
foreach($name in @('latest-first-forest-release.txt','latest-forest-release.txt','latest-allium-release.txt','latest-release.txt')){$release | Set-Content (Join-Path $root "dist/$name")}
Write-Host "First Forest playtest: $release"
