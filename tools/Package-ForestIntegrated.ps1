$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root 'playtest/ForestIntegrated'
$evidence=Join-Path $root 'artifacts/validation/forest-integrated'
$base=(Get-Content (Join-Path $root 'artifacts/forest-integrated-base.txt') -Raw).Trim()
$report=Get-Content (Join-Path $evidence 'content.json') -Raw|ConvertFrom-Json
if($report.result -ne 'PASS'){throw 'Integrated config validation required'}
foreach($name in @('core','roster','runtime','horde','warden','heavy','timeline','damage','reload')) {
 $text=Get-Content (Join-Path $evidence ($name+'.txt')) -Raw
 if($text -notmatch 'PASS' -or $text -match '\] FAIL'){throw "Missing passing evidence: $name"}
}
$pois=Get-Content (Join-Path $evidence 'pois.txt') -Raw
if(([regex]::Matches($pois,'\[Integrated\] PASS POI')).Count -ne 15 -or $pois -match '\] FAIL'){throw 'All fifteen POIs must pass'}
$snapshot=Get-Content (Join-Path $evidence 'tested-mods.json') -Raw|ConvertFrom-Json
foreach($entry in $snapshot) {
 if((Get-FileHash (Join-Path $profile ('Mods/'+$entry.path))).Hash -ne $entry.sha256){throw "Tested mod changed: $($entry.path)"}
}
$release=Join-Path $root ('dist/Delve-Forest-Integrated-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $release,(Join-Path $release 'Mods') -Force|Out-Null
foreach($mod in $report.mods){Copy-Item -LiteralPath (Join-Path $profile ('Mods/'+$mod)) -Destination (Join-Path $release 'Mods') -Recurse}
Copy-Item -LiteralPath (Join-Path $base 'Worlds') -Destination $release -Recurse
foreach($name in @('Play-Allium.cmd','Play-Allium.ps1','Verify-Package.ps1','world-name.txt')){Copy-Item -LiteralPath (Join-Path $base $name) -Destination $release}
Copy-Item -LiteralPath (Join-Path $root 'docs/forest-integrated-playtest.txt') -Destination (Join-Path $release 'START-HERE.txt')
Copy-Item -LiteralPath (Join-Path $root 'docs/forest-integrated-validation.txt') -Destination (Join-Path $release 'VALIDATION.txt')
Copy-Item -LiteralPath (Join-Path $root 'docs/forest-pantry-playtest.txt') -Destination (Join-Path $release 'PANTRY.txt')
Copy-Item -LiteralPath (Join-Path $root 'docs/first-tier-playtest.txt') -Destination (Join-Path $release 'PROGRESSION.txt')
Copy-Item -LiteralPath $evidence -Destination (Join-Path $release 'Evidence') -Recurse
foreach($name in @('Catalogue','FARMING.txt','FOREST-BASELINE.txt')){if(Test-Path (Join-Path $base $name)){Copy-Item -LiteralPath (Join-Path $base $name) -Destination $release -Recurse}}
Copy-Item -LiteralPath (Join-Path $base 'Evidence/validation-summary.txt') -Destination (Join-Path $release 'BASE-VALIDATION.txt')
$manifest=@{name='Allium Integrated Forest';version='0.4.2-dev-enemies';gameVersion='3.3.0 (b18)';baseRelease=(Split-Path $base -Leaf);files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File|Sort-Object FullName|ForEach-Object{@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
foreach($pointer in @('latest-integrated-release.txt','latest-allium-release.txt','latest-release.txt','latest-forest-bestiary-release.txt')){$release|Set-Content (Join-Path $root ('dist/'+$pointer)) -Encoding utf8}
Write-Host "Integrated Forest release: $release"
