param([string]$ProfileName='ForestM2')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root "playtest/$ProfileName"
$evidence=Join-Path $root 'artifacts/validation/processing-runtime.txt'
$runtime=Get-Content $evidence -Raw
if($runtime -notmatch 'RELOAD VERIFIED' -or $runtime -notmatch 'HEALING PASS' -or $runtime -notmatch '\[Pantry\] PASS 22' -or $runtime -notmatch '\[Farming\] PASS' -or $runtime -match '\[(Processing|Pantry|Farming)\] FAIL') {throw 'Passing integrated runtime evidence required'}
if(([regex]::Matches($runtime,'PASS: [0-9]+ loaded content')).Count -lt 2 -or ([regex]::Matches($runtime,'\[Processing\] PASS')).Count -lt 2){throw 'Initial and reload production checks must pass'}
$catalogue=Get-Content (Join-Path $root 'artifacts/validation/forest-catalogue.json') -Raw | ConvertFrom-Json
if($catalogue.result -ne 'PASS'){throw 'Catalogue checks must pass'}
$snapshot=Get-Content (Join-Path $root 'artifacts/validation/processing-tested-mods.json') -Raw | ConvertFrom-Json
foreach($entry in $snapshot) {
 if((Get-FileHash (Join-Path $profile ('Mods/'+$entry.path))).Hash -ne $entry.sha256){throw "Tested file changed: $($entry.path)"}
}
$release=Join-Path $root ('dist/Delve-Forest-M2-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory (Join-Path $release 'Mods'),(Join-Path $release 'Worlds'),(Join-Path $release 'Catalogue'),(Join-Path $release 'Evidence') -Force | Out-Null
foreach($name in @('Delve','DelveWayrest','DelveWildlife','ZDelveForest')) {
 Copy-Item -LiteralPath (Join-Path $profile "Mods/$name") -Destination (Join-Path $release 'Mods') -Recurse
}
$base=(Get-Content (Join-Path $profile 'base-release.txt') -Raw).Trim()
Copy-Item -LiteralPath (Join-Path $base 'Worlds/Allium-v0.9') -Destination (Join-Path $release 'Worlds') -Recurse
foreach($name in @('Play-Allium.cmd','Play-Allium.ps1','Verify-Package.ps1')) {Copy-Item (Join-Path $PSScriptRoot "package/$name") $release}
'Allium-v0.9' | Set-Content (Join-Path $release 'world-name.txt')
Copy-Item (Join-Path $root 'docs/forest-processing-playtest.txt') (Join-Path $release 'START-HERE.txt')
Copy-Item (Join-Path $root 'src/Forest/processing.json') (Join-Path $release 'Catalogue')
Copy-Item (Join-Path $root 'src/Forest/catalogue.json') (Join-Path $release 'Catalogue')
Copy-Item (Join-Path $root 'docs/forest-crafting-catalogue.txt') (Join-Path $release 'Catalogue')
Copy-Item (Join-Path $root 'docs/forest-level-20-roadmap.txt') (Join-Path $release 'Catalogue')
foreach($name in @('processing-runtime.txt','processing-tested-mods.json','forest-catalogue.json','processing-static.json','forest-m2-build.txt')) {
 Copy-Item (Join-Path $root "artifacts/validation/$name") (Join-Path $release 'Evidence')
}
$manifest=@{name='Delve Forest M2 Processing';version='0.5.0-dev';gameVersion='3.3.0 (b18)';baseRelease=(Split-Path $base -Leaf);files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File | Sort-Object FullName | ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release | Set-Content (Join-Path $root 'dist/latest-forest-release.txt')
Write-Host "Unified Forest build: $release"
