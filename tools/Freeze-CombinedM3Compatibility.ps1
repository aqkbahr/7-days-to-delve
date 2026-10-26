$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$old=(Get-Content (Join-Path $root 'dist/latest-combined-m3-candidate.txt') -Raw).Trim()
$release=Join-Path $root ('dist/Delve-Combined-M3-CANDIDATE-'+(Get-Date -Format yyyyMMdd-HHmmss))
Copy-Item -LiteralPath $old -Destination $release -Recurse
Copy-Item (Join-Path $root 'playtest/CombinedM3/Mods/Delve/DelveSpellVisibility.dll') (Join-Path $release 'Mods/Delve') -Force
Copy-Item (Join-Path $PSScriptRoot 'compatibility/CombinedM3SpellVisibility.cs') (Join-Path $release 'Evidence/SpellVisibilityCompatibility.cs') -Force
$sources=Get-Content (Join-Path $release 'sources.json') -Raw|ConvertFrom-Json
$sources.spellCompatibility='DelveSpellVisibility.dll: target collider ownership and scoped burst-source exclusion; native walls remain opaque. Pending integrated regression.'
$sources|ConvertTo-Json|Set-Content (Join-Path $release 'sources.json') -Encoding utf8
$manifest=Get-Content (Join-Path $release 'manifest.json') -Raw|ConvertFrom-Json
$manifest.files=@(Get-ChildItem $release -Recurse -File|Where-Object {$_.FullName -ne (Join-Path $release 'manifest.json')}|Sort-Object FullName|ForEach-Object{@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release|Set-Content (Join-Path $root 'dist/latest-combined-m3-candidate.txt') -Encoding utf8
& 'C:/Users/Michael/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' (Join-Path $PSScriptRoot 'validate_forest_integrated.py') --profile CombinedM3 --baseline $release --evidence combined-m3
if($LASTEXITCODE -ne 0){throw 'Combined content validation failed'}
