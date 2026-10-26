param([Parameter(Mandatory=$true)][string]$TerrainDll,[Parameter(Mandatory=$true)][string]$TerrainSource)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$previous=(Get-Content (Join-Path $root 'dist/latest-combined-m3-candidate.txt') -Raw).Trim()
& (Join-Path $previous 'Verify-Package.ps1')
$dll=(Resolve-Path -LiteralPath $TerrainDll).Path
$source=(Resolve-Path -LiteralPath $TerrainSource).Path
$release=Join-Path $root ('dist/Delve-Combined-Latest-CANDIDATE-'+(Get-Date -Format yyyyMMdd-HHmmss))
Copy-Item -LiteralPath $previous -Destination $release -Recurse
Copy-Item -LiteralPath $dll -Destination (Join-Path $release 'Mods/Delve/DelveTerrainCompatibility.dll') -Force
Copy-Item -LiteralPath $source -Destination (Join-Path $release 'Evidence/TerrainCompatibility.cs') -Force
$provenance=Get-Content (Join-Path $release 'sources.json') -Raw | ConvertFrom-Json
$provenance | Add-Member -NotePropertyName terrainCompatibility -NotePropertyValue @{source=$source;sha256=(Get-FileHash $dll).Hash;previousCandidate=$previous;acceptance='PENDING expanded native generation, sparse clone, decoder and integrated checks'} -Force
$provenance | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'sources.json') -Encoding utf8
'PENDING: final combined acceptance after native sparse-cell clone correction.' | Set-Content (Join-Path $release 'VALIDATION.txt')
$manifest=@{name='Allium Latest Combined Candidate';version='0.7.2-dev-candidate';gameVersion='3.3.0 (b18)';acceptance='PENDING';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File | Where-Object {$_.FullName -ne (Join-Path $release 'manifest.json')} | Sort-Object FullName | ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release | Set-Content (Join-Path $root 'dist/latest-combined-m3-candidate.txt') -Encoding utf8
Write-Host "Frozen candidate: $release"
