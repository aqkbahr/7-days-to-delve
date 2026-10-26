$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$combined=Join-Path $root 'dist/Delve-Combined-Playtest-20261024-220742'
$m3=Join-Path $root 'dist/Delve-Forest-M3-20261024-220158'
foreach($source in @($combined,$m3)){& (Join-Path $source 'Verify-Package.ps1')}
$release=Join-Path $root ('dist/Delve-Combined-M3-CANDIDATE-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory $release,(Join-Path $release 'Mods') -Force|Out-Null
Get-ChildItem $combined|Where-Object Name -notin @('Mods','Catalogue','manifest.json')|ForEach-Object {Copy-Item -LiteralPath $_.FullName -Destination $release -Recurse}
foreach($name in @('Delve','DelveWayrest','DelveWildlife','ZDelveDungeons','ZDelveForest')){
 $source=if($name -eq 'Delve'){$m3}else{$combined}
 Copy-Item -LiteralPath (Join-Path $source ('Mods/'+$name)) -Destination (Join-Path $release 'Mods') -Recurse
}
Copy-Item -LiteralPath (Join-Path $m3 'Catalogue') -Destination $release -Recurse
Copy-Item -LiteralPath (Join-Path $m3 'Evidence') -Destination (Join-Path $release 'Evidence/M3Source') -Recurse
Copy-Item (Join-Path $m3 'START-HERE.txt') (Join-Path $release 'M3-EQUIPMENT-SPELLS.txt')
Copy-Item (Join-Path $m3 'FIRST-PLAYTEST.txt') (Join-Path $release 'M3-PLAYTEST.txt')
'UNVALIDATED M3 COMBINED CANDIDATE. Previous acceptance evidence is historical. Do not use as the promoted playtest until combined tests pass.'|Set-Content (Join-Path $release 'START-HERE.txt')
'PENDING: M3 core with v0.10 map, repaired delves, early enemies and horde module.'|Set-Content (Join-Path $release 'VALIDATION.txt')
$sources=Get-Content (Join-Path $release 'sources.json') -Raw|ConvertFrom-Json
$sources.core=$m3
$sources|Add-Member -NotePropertyName combinedBase -NotePropertyValue $combined -Force
$sources.engineValidation='PENDING: integrated M3 acceptance'
$sources|ConvertTo-Json|Set-Content (Join-Path $release 'sources.json') -Encoding utf8
$manifest=@{name='Allium Combined M3 Candidate';version='0.6.1-dev-candidate';gameVersion='3.3.0 (b18)';acceptance='PENDING';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File|Sort-Object FullName|ForEach-Object{@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release|Set-Content (Join-Path $root 'dist/latest-combined-m3-candidate.txt') -Encoding utf8
Write-Host "M3 combined candidate: $release"
