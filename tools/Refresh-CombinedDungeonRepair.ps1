$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$old=(Get-Content (Join-Path $root 'dist/latest-combined-candidate.txt') -Raw).Trim()
$repair=Join-Path $root 'dist/Delve-Allium-v0.10-20261024-212717'
foreach($package in @($old,$repair)){& (Join-Path $package 'Verify-Package.ps1')}
$allowed=@('Prefabs/POIs/delve_dungeon_cave_12.tts','Prefabs/POIs/delve_dungeon_cave_12.blocks.nim','Prefabs/POIs/delve_dungeon_cave_12.xml')
foreach($mod in @('DelveWayrest','ZDelveDungeons')) {
 $source=Join-Path $repair ('Mods/'+$mod)
 foreach($file in Get-ChildItem $source -Recurse -File){
  $relative=$file.FullName.Substring($source.Length+1).Replace('\','/')
  $before=Join-Path $old ('Mods/'+$mod+'/'+$relative)
  if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash $before).Hash -and !($mod -eq 'DelveWayrest' -and $relative -in $allowed)){throw "Unexpected map module change: $mod/$relative"}
 }
}
$release=Join-Path $root ('dist/Delve-Combined-CANDIDATE-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
Copy-Item -LiteralPath $old -Destination $release -Recurse
foreach($relative in $allowed){Copy-Item -LiteralPath (Join-Path $repair ('Mods/DelveWayrest/'+$relative)) -Destination (Join-Path $release ('Mods/DelveWayrest/'+$relative)) -Force}
Copy-Item (Join-Path $repair 'VALIDATION.txt') (Join-Path $release 'Evidence/DungeonRepair.txt')
Copy-Item (Join-Path $repair 'START-HERE.txt') (Join-Path $release 'DUNGEONS.txt') -Force
Copy-Item (Join-Path $repair 'old-warden-supports.xml') $release
$sources=Get-Content (Join-Path $release 'sources.json') -Raw|ConvertFrom-Json
$sources|Add-Member -NotePropertyName dungeonRepair -NotePropertyValue $repair -Force
$sources.engineValidation='PENDING: combined dungeon acceptance after three-file prefab repair; unchanged enemy/core checks retained'
$sources|ConvertTo-Json|Set-Content (Join-Path $release 'sources.json') -Encoding utf8
$manifest=Get-Content (Join-Path $release 'manifest.json') -Raw|ConvertFrom-Json
$manifest.files=@(Get-ChildItem $release -Recurse -File|Where-Object {$_.FullName -ne (Join-Path $release 'manifest.json')}|Sort-Object FullName|ForEach-Object{@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release|Set-Content (Join-Path $root 'dist/latest-combined-candidate.txt') -Encoding utf8
Write-Host "Repaired combined candidate: $release"
