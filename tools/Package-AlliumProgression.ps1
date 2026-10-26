$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
# Pin independently tested inputs; do not rebuild moving shared source here.
$core=Join-Path $root 'dist/Delve-Forest-M3-20261024-220158'
$map=Join-Path $root 'dist/Delve-Combined-CANDIDATE-20261024-215746'
foreach($source in @($core,$map)){& (Join-Path $source 'Verify-Package.ps1')}
$release=Join-Path $root ('dist/Delve-Allium-Progression-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $release,(Join-Path $release 'Mods'),(Join-Path $release 'Evidence') -Force|Out-Null
foreach($mod in @('Delve','DelveWildlife')){Copy-Item (Join-Path $core "Mods/$mod") (Join-Path $release 'Mods') -Recurse}
foreach($mod in @('DelveWayrest','ZDelveDungeons','ZDelveForest')){Copy-Item (Join-Path $map "Mods/$mod") (Join-Path $release 'Mods') -Recurse}
Copy-Item (Join-Path $map 'Worlds') $release -Recurse
foreach($name in @('Play-Allium.cmd','Play-Allium.ps1','Verify-Package.ps1','world-name.txt','dungeons-atlas.png','dungeons.json','locations-atlas.png','locations.json','resource-atlas.png','resource-sites.json')){Copy-Item (Join-Path $map $name) $release}
Copy-Item (Join-Path $core 'Catalogue') $release -Recurse
Copy-Item (Join-Path $core 'Evidence') (Join-Path $release 'Evidence/EquipmentAndCrafting') -Recurse
foreach($name in @('FIRST-PLAYTEST.txt','PROCESSING-GUIDE.txt')){Copy-Item (Join-Path $core $name) $release}
Copy-Item (Join-Path $root 'docs/first-tier-playtest.txt') (Join-Path $release 'PROGRESSION.txt')
$guide=Get-Content (Join-Path $release 'PROGRESSION.txt') -Raw
$guide=$guide -replace 'Run Play-Delve.cmd in the first-tier package\. Requires 7 Days to Die 3\.3\.0 \(b18\),\r?\nwith EAC disabled\. Create a fresh Navezgane test game\. The package uses isolated\r?\nsaves and does not contain the Allium world or replace the validated release\.',"Run Play-Allium.cmd in this combined package. Requires 7 Days to Die 3.3.0 (b18),`nwith EAC disabled. Create a fresh Allium-v0.10 game. The package includes Allium,`nuses isolated saves and preserves earlier release folders."
$guide|Set-Content (Join-Path $release 'PROGRESSION.txt')
(Get-Content (Join-Path $release 'FIRST-PLAYTEST.txt') -Raw).Replace('Allium-v0.9','Allium-v0.10')|Set-Content (Join-Path $release 'FIRST-PLAYTEST.txt')
Copy-Item (Join-Path $root 'docs/allium-progression-playtest.txt') (Join-Path $release 'START-HERE.txt')
Copy-Item (Join-Path $root 'docs/forest-combined-validation.txt') (Join-Path $release 'Evidence/PreviousDungeonAndEnemyValidation.txt')
@{core=$core;worldAndSettlementsAndEnemies=$map;acceptance='Awaiting combined progression smoke test'}|ConvertTo-Json|Set-Content (Join-Path $release 'sources.json')
$manifest=@{name='Allium with first-tier progression and Forged equipment';version='0.6.1-dev';gameVersion='3.3.0 (b18)';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File|Sort-Object FullName|ForEach-Object{@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release|Set-Content (Join-Path $root 'artifacts/allium-progression-package.txt')
Write-Host "Assembled combined playtest: $release"
