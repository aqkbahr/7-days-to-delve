param([string]$ProfileName='AlliumFarming')
$ErrorActionPreference='Stop'
if($ProfileName -notmatch '^[A-Za-z0-9_-]+$'){throw 'Invalid profile name'}
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root ('playtest/'+$ProfileName)
$sources=Get-Content (Join-Path $profile 'integration-sources.json') -Raw | ConvertFrom-Json
$evidence=Join-Path $root 'artifacts/validation/allium-farming'
$runtime=Get-Content (Join-Path $evidence 'runtime.txt') -Raw
if($runtime -notmatch '\[Farming\] PASS ' -or $runtime -notmatch 'PASS: [0-9]+ loaded content' -or $runtime -match '\[Farming\] FAIL'){throw 'Passing combined engine evidence required'}
if((Get-Content (Join-Path $evidence 'content.json') -Raw | ConvertFrom-Json).result -ne 'PASS'){throw 'Integration checks required'}
$snapshot=Get-Content (Join-Path $evidence 'tested-mods.json') -Raw | ConvertFrom-Json
foreach($entry in $snapshot) {
    if((Get-FileHash (Join-Path $profile ('Mods/'+$entry.path))).Hash.ToLowerInvariant() -ne $entry.sha256){throw "Tested mod changed: $($entry.path)"}
}
$release=Join-Path $root ('dist/Delve-Allium-Farming-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $release,(Join-Path $release 'Mods'),(Join-Path $release 'Worlds'),(Join-Path $release 'Evidence') -Force|Out-Null
foreach($name in @('Delve','DelveWayrest','DelveWildlife','ZDelveForest')) {
    Copy-Item -LiteralPath (Join-Path $profile ('Mods/'+$name)) -Destination (Join-Path $release 'Mods') -Recurse
}
Copy-Item -LiteralPath (Join-Path $sources.baseRelease ('Worlds/'+$sources.world)) -Destination (Join-Path $release 'Worlds') -Recurse
Copy-Item -LiteralPath (Join-Path $profile 'Catalogue') -Destination $release -Recurse
foreach($name in @('Play-Allium.cmd','Play-Allium.ps1','Verify-Package.ps1')) {
    Copy-Item -LiteralPath (Join-Path $sources.baseRelease $name) -Destination $release
}
$sources.world | Set-Content (Join-Path $release 'world-name.txt')
Copy-Item -LiteralPath (Join-Path $root 'docs/allium-farming-playtest.txt') -Destination (Join-Path $release 'START-HERE.txt')
Copy-Item -LiteralPath (Join-Path $root 'docs/farming-first-pass.txt') -Destination (Join-Path $release 'FARMING.txt')
Copy-Item -LiteralPath (Join-Path $sources.baseRelease 'START-HERE.txt') -Destination (Join-Path $release 'FOREST-BASELINE.txt')
Copy-Item (Join-Path $evidence '*') (Join-Path $release 'Evidence')
$manifest=@{name='Delve Allium Farming';version='0.4.1-dev-farming';gameVersion='3.3.0 (b18)';world=$sources.world;baseRelease=(Split-Path $sources.baseRelease -Leaf);files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File | Sort-Object FullName | ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release | Set-Content (Join-Path $root 'dist/latest-allium-farming-release.txt')
$release | Set-Content (Join-Path $root 'dist/latest-allium-release.txt')
Write-Host "Allium farming release: $release"
