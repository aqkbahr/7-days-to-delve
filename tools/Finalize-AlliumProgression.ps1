$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$release=(Get-Content (Join-Path $root 'artifacts/allium-progression-package.txt') -Raw).Trim()
$evidence=Join-Path $root 'artifacts/validation/allium-progression'
$profile=Join-Path $root 'playtest/AlliumProgression'
$required=@{core='PASS: 614';forged='\[Forged\] PASS';processing='\[Processing\] PASS';enemies='\[Forest\] PASS';integration='\[Integrated\] PASS';dungeons='\[Dungeons\] PASS'}
foreach($name in $required.Keys){
 $text=Get-Content (Join-Path $evidence "$name.txt") -Raw
 if($text -notmatch $required[$name] -or $text -match '\] FAIL|Exception'){throw "Runtime check missing or failed: $name"}
}
$snapshot=Get-Content (Join-Path $evidence 'tested-mods.json') -Raw|ConvertFrom-Json
foreach($entry in $snapshot){foreach($folder in @($release,$profile)){
 if((Get-FileHash (Join-Path $folder ('Mods/'+$entry.path))).Hash -ne $entry.sha256){throw "Tested content changed: $($entry.path)"}
}}
$actual=@(Get-ChildItem (Join-Path $release 'Mods') -Recurse -File)
if($actual.Count -ne $snapshot.Count){throw 'Production file inventory changed'}
$report=Get-Content (Join-Path $evidence 'content.json') -Raw|ConvertFrom-Json
if($report.result -ne 'PASS' -or $report.mods.Count -ne 5){throw 'Combined static validation must pass'}
Copy-Item $evidence (Join-Path $release 'Evidence/CombinedProgression') -Recurse
$sources=Get-Content (Join-Path $release 'sources.json') -Raw|ConvertFrom-Json
$sources.acceptance='PASS: combined Allium startup, progression, equipment/spells, processing and enemy fixtures. Human playthrough, full dungeon reacceptance and multiplayer remain.'
$sources|ConvertTo-Json|Set-Content (Join-Path $release 'sources.json')
$manifest=Get-Content (Join-Path $release 'manifest.json') -Raw|ConvertFrom-Json
$manifest.files=@(Get-ChildItem $release -Recurse -File|Where-Object {$_.FullName -ne (Join-Path $release 'manifest.json')}|Sort-Object FullName|ForEach-Object{@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release|Set-Content (Join-Path $root 'dist/latest-allium-progression-release.txt')
Write-Host "Combined progression playtest ready: $release"
