$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if((Get-Content (Join-Path $root 'artifacts/validation/first-tier-runtime.txt') -Raw) -notmatch 'PASS:') { throw 'A passing first-tier runtime check is required.' }
$release=Join-Path $root ('dist/Delve-First-Tier-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path (Join-Path $release 'Mods') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $root 'src/Delve') -Destination (Join-Path $release 'Mods') -Recurse
foreach($name in @('Play-Delve.cmd','Play-Delve.ps1','Verify-Package.ps1')) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot ('package/'+$name)) -Destination $release }
Copy-Item -LiteralPath (Join-Path $root 'docs/first-tier-playtest.txt') -Destination (Join-Path $release 'START-HERE.txt')
foreach($name in @('progression-coverage.json','first-tier-runtime.txt','first-tier-equipment.txt')) { Copy-Item -LiteralPath (Join-Path $root ('artifacts/validation/'+$name)) -Destination $release }
Copy-Item -LiteralPath (Join-Path $root 'artifacts/tests/first-tier-results.txt') -Destination $release
$manifest=@{name='Delve first-tier development playtest';version='0.3.0-dev';gameVersion='3.3.0 (b18)';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File | Sort-Object FullName | ForEach-Object { @{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash} })
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release | Set-Content (Join-Path $root 'artifacts/validation/first-tier-package-path.txt') -Encoding utf8
Write-Host "First-tier development playtest: $release"
