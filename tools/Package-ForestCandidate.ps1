# Prepare a combined candidate when engine acceptance is blocked. This never
# advances the tested-release pointers and never substitutes for runtime tests.
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$core=Join-Path $root 'dist/Delve-Forest-M2-20261024-205143'
$map=Join-Path $root 'dist/Delve-Allium-v0.10-20261024-205532'
foreach($source in @($core,$map)){& (Join-Path $source 'Verify-Package.ps1')}
$release=Join-Path $root ('dist/Delve-Combined-CANDIDATE-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $release,(Join-Path $release 'Mods'),(Join-Path $release 'Evidence') -Force|Out-Null
foreach($mod in @('Delve','DelveWildlife')){Copy-Item -LiteralPath (Join-Path $core ('Mods/'+$mod)) -Destination (Join-Path $release 'Mods') -Recurse}
foreach($mod in @('DelveWayrest','ZDelveDungeons')){Copy-Item -LiteralPath (Join-Path $map ('Mods/'+$mod)) -Destination (Join-Path $release 'Mods') -Recurse}
Copy-Item -LiteralPath (Join-Path $root 'src/ZDelveForest') -Destination (Join-Path $release 'Mods') -Recurse
Copy-Item -LiteralPath (Join-Path $map 'Worlds') -Destination $release -Recurse
foreach($name in @('Play-Allium.cmd','Play-Allium.ps1','Verify-Package.ps1','world-name.txt','dungeons-atlas.png','dungeons.json','locations-atlas.png','locations.json','resource-atlas.png','resource-sites.json')){Copy-Item -LiteralPath (Join-Path $map $name) -Destination $release}
Copy-Item -LiteralPath (Join-Path $core 'Catalogue') -Destination $release -Recurse
Copy-Item -LiteralPath (Join-Path $core 'Evidence') -Destination (Join-Path $release 'Evidence/Processing') -Recurse
Copy-Item -LiteralPath (Join-Path $map 'VALIDATION.txt') -Destination (Join-Path $release 'Evidence/Dungeons.txt')
Copy-Item -LiteralPath (Join-Path $root 'artifacts/validation/forest-integrated') -Destination (Join-Path $release 'Evidence/EnemyEarlierBaseline') -Recurse
Copy-Item -LiteralPath (Join-Path $root 'docs/forest-combined-candidate.txt') -Destination (Join-Path $release 'START-HERE.txt')
Copy-Item -LiteralPath (Join-Path $core 'START-HERE.txt') -Destination (Join-Path $release 'PROCESSING.txt')
Copy-Item -LiteralPath (Join-Path $map 'START-HERE.txt') -Destination (Join-Path $release 'DUNGEONS.txt')
Copy-Item -LiteralPath (Join-Path $root 'docs/farming-first-pass.txt') -Destination (Join-Path $release 'FARMING.txt') -ErrorAction SilentlyContinue
$sources=@{core=$core;map=$map;enemySource='src/ZDelveForest';engineValidation='BLOCKED: Steam installation incomplete';gameTarget='3.3.0 (b18)'}
$sources|ConvertTo-Json|Set-Content (Join-Path $release 'sources.json') -Encoding utf8
$manifest=@{name='Allium Combined Candidate';version='0.5.1-dev-enemies-candidate';gameVersion='3.3.0 (b18)';acceptance='INCOMPLETE - do not treat integrity checks as engine validation';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File|Sort-Object FullName|ForEach-Object{@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release|Set-Content (Join-Path $root 'dist/latest-combined-candidate.txt') -Encoding utf8
Write-Host "UNVALIDATED combined candidate: $release"
