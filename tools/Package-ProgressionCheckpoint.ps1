$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$release=Join-Path $root ('dist/Delve-Progression-Checkpoint-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path (Join-Path $release 'Mods') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $root 'src/Delve') -Destination (Join-Path $release 'Mods') -Recurse
Copy-Item (Join-Path $PSScriptRoot 'package/*') $release
Copy-Item -LiteralPath (Join-Path $root 'docs/progression-implementation-checkpoint.txt') -Destination (Join-Path $release 'START-HERE.txt')
Copy-Item -LiteralPath (Join-Path $root 'artifacts/validation/progression-coverage.json') -Destination $release
Copy-Item -LiteralPath (Join-Path $root 'artifacts/validation/progression-runtime.txt') -Destination $release
$manifest=@{name='Delve progression INCOMPLETE development checkpoint';version='0.3.0-dev';gameVersion='3.3.0 (b18)';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File | Sort-Object FullName | ForEach-Object { @{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash} })
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release | Set-Content (Join-Path $root 'artifacts/validation/progression-checkpoint-path.txt') -Encoding utf8
Write-Host "Development checkpoint only: $release"
# Deliberately do not change any latest-release pointer.
