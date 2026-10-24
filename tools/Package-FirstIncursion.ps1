$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$source=(Get-Content (Join-Path $root 'dist/latest-allium-release.txt') -Raw).Trim()
& (Join-Path $source 'Verify-Package.ps1')
$release=Join-Path $root ('dist/Delve-FirstIncursion-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $release,(Join-Path $release 'Mods') -Force | Out-Null
# Reuse the previously validated map inputs, never a played world's saves.
Copy-Item (Join-Path $source 'Worlds') $release -Recurse
Copy-Item (Join-Path $source 'world-name.txt') $release
foreach($name in @('Play-Allium.cmd','Play-Allium.ps1','Verify-Package.ps1')) { Copy-Item (Join-Path $PSScriptRoot "package/$name") $release }
foreach($name in @('Delve','DelveWayrest')) { Copy-Item (Join-Path $root "src/$name") (Join-Path $release 'Mods') -Recurse }
Copy-Item (Join-Path $root 'docs/first-incursion.txt') (Join-Path $release 'START-HERE.txt')
Copy-Item (Join-Path $root 'docs/first-incursion-validation.txt') (Join-Path $release 'VALIDATION.txt')
Copy-Item (Join-Path $root 'docs/wayrest-campaign-playtest.txt') $release
$manifest=@{name='7 Days to Delve - First Incursion playtest';version='first-incursion-1';gameVersion='3.3.0 (b18)';mapSource=(Split-Path $source -Leaf);files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File | Sort-Object FullName | ForEach-Object { @{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash} })
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release | Set-Content (Join-Path $root 'dist/latest-incursion-release.txt') -Encoding utf8
Write-Host "First incursion package: $release"
