$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$old=(Get-Content (Join-Path $root 'dist/latest-combined-candidate.txt') -Raw).Trim()
$profile=Join-Path $root 'playtest/ForestCombined10'
$repair=Get-Content (Join-Path $root 'artifacts/validation/forest-combined10-dungeons/torch-repair.txt') -Raw
if($repair -notmatch 'PASS torch repair' -or $repair -match '\[Dungeons\] FAIL'){throw 'Verified native serialization required'}
$recorded=Get-Process -Id ([int](Get-Content (Join-Path $profile 'server.pid'))) -ErrorAction SilentlyContinue
if($recorded -and $recorded.ProcessName -eq '7DaysToDie'){throw 'Shut down authoring server before packaging'}
& (Join-Path $old 'Verify-Package.ps1')
$release=Join-Path $root ('dist/Delve-Combined-CANDIDATE-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
Copy-Item -LiteralPath $old -Destination $release -Recurse
foreach($ext in @('tts','blocks.nim','xml')){
 $relative="DelveWayrest/Prefabs/POIs/delve_dungeon_cave_11.$ext"
 $fixed=Join-Path $profile ('Mods/'+$relative)
 Copy-Item -LiteralPath $fixed -Destination (Join-Path $release ('Mods/'+$relative)) -Force
 # Keep future map builds from reintroducing the original decorative assembly.
 foreach($base in @('src','playtest/DungeonAuthor/Mods')){
  $target=Join-Path $root ($base+'/'+$relative)
  if(Test-Path $target){
   $hash=(Get-FileHash $target).Hash
   if($hash -ne (Get-FileHash (Join-Path $old ('Mods/'+$relative))).Hash -and $hash -ne (Get-FileHash $fixed).Hash){throw "Concurrent prefab change: $target"}
   Copy-Item -LiteralPath $fixed -Destination $target -Force
  }
 }
}
Copy-Item (Join-Path $root 'artifacts/validation/forest-combined10-dungeons/torch-repair.txt') (Join-Path $release 'Evidence/SmugglerTorchRepair.txt')
$sources=Get-Content (Join-Path $release 'sources.json') -Raw|ConvertFrom-Json
$sources|Add-Member -NotePropertyName smugglerRepair -NotePropertyValue 'Three unsupported decorative torch/post cells removed; native save/reload verified; all other cells and quest metadata retained' -Force
$sources.engineValidation='PENDING: fresh-save combined dungeon acceptance after Smuggler torch repair'
$sources|ConvertTo-Json|Set-Content (Join-Path $release 'sources.json') -Encoding utf8
$manifest=Get-Content (Join-Path $release 'manifest.json') -Raw|ConvertFrom-Json
$manifest.files=@(Get-ChildItem $release -Recurse -File|Where-Object {$_.FullName -ne (Join-Path $release 'manifest.json')}|Sort-Object FullName|ForEach-Object{@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release|Set-Content (Join-Path $root 'dist/latest-combined-candidate.txt') -Encoding utf8
Write-Host "Smuggler repair candidate: $release"
