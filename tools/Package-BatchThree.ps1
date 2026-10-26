$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if(Get-Process 7DaysToDie -ErrorAction SilentlyContinue){throw 'Close test processes before installing'}
$previous=(Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim()
& (Join-Path $previous 'Verify-Package.ps1')
$candidate=Join-Path $root 'artifacts/batch-03/candidate'
$evidence=Join-Path $root 'artifacts/validation/batch03'
foreach($name in @('onboarding','rank20','recipes','core','integration','recruit-definitions','recruit-flow','resurrection','horde','incursion')){
 $result=Get-Content (Join-Path $evidence ($name+'.txt')) -Raw
 if($result -notmatch 'PASS' -or $result -match '\] FAIL|^FAIL'){throw "Acceptance missing: $name"}
}
foreach($name in @('ui','world')){if((Get-Content (Join-Path $evidence ($name+'.txt')) -Raw) -notmatch 'PASS COMPLETE'){throw "Native client acceptance missing: $name"}}
$audit=Get-Content (Join-Path $evidence 'migration-reload.txt') -Raw
if($audit -notmatch 'eligible=0' -or $audit -notmatch 'crate storage added=0' -or $audit -match 'FAIL'){throw 'Migration reload has pending changes'}
$tested=Get-Content (Join-Path $evidence 'tested-mods-reload.json') -Raw|ConvertFrom-Json
$worldTested=Get-Content (Join-Path $evidence 'world-tested-mods.json') -Raw|ConvertFrom-Json
foreach($f in $worldTested){if((Get-FileHash (Join-Path $candidate $f.path)).Hash -ne $f.sha256){throw "Candidate differs from native world acceptance: $($f.path)"}}
foreach($f in $tested){if((Get-FileHash (Join-Path $candidate $f.path)).Hash -ne $f.sha256 -and $f.path -notmatch '^Mods/DelveWayrest/Prefabs/POIs/delve_wayrest_forest\.(tts|blocks\.nim|xml)$'){throw "Candidate differs from server regression suite: $($f.path)"}}
$data=(Get-Content (Join-Path $root 'artifacts/batch-03/original-data-location.txt') -Raw).Trim()
$save=Join-Path $data 'Saves/Allium-v0.10/ForestTest01'
$backup=(Get-Content (Join-Path $root 'artifacts/batch-03/preflight-backup.txt') -Raw).Trim()
$original=Join-Path $backup 'Saves/Allium-v0.10/ForestTest01'
foreach($f in Get-ChildItem $original -Recurse -File){$relative=$f.FullName.Substring($original.Length+1);if((Get-FileHash $f.FullName).Hash -ne (Get-FileHash (Join-Path $save $relative)).Hash){throw "Playable save changed: $relative"}}
$preserved=@(Get-ChildItem $save -Recurse -File|Where-Object {$_.FullName -notlike "$save\Region\*" -and $_.Name -ne 'blockmappings.nim'}|ForEach-Object {@{path=$_.FullName;hash=(Get-FileHash $_.FullName).Hash}})
$release=Join-Path $root ('dist/Delve-Batch03-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
Copy-Item $previous $release -Recurse
foreach($m in Get-ChildItem (Join-Path $candidate 'Mods') -Directory){Copy-Item $m.FullName (Join-Path $release 'Mods') -Recurse -Force}
Copy-Item (Join-Path $root 'docs/playtest-batch-03.txt') (Join-Path $release 'BATCH-03.txt')
New-Item -ItemType Directory (Join-Path $release 'Evidence/Batch03') -Force|Out-Null
Copy-Item (Join-Path $evidence '*') (Join-Path $release 'Evidence/Batch03') -Force
"BATCH 03 - 0.10.5`r`nContinue ForestTest01 in Allium-v0.10. Character, quests and stored supplies are preserved.`r`nRead BATCH-03.txt for changes and playtest checks. Crafting tomes and Pitch remain installed.`r`n"|Set-Content (Join-Path $release 'START-HERE.txt')
$launcher=Join-Path $release 'Play-Allium.ps1';(Get-Content $launcher -Raw).Replace('Crafting tomes installed:','Batch 03 installed:').Replace('-GameName=AlliumExpedition','-GameName=ForestTest01')|Set-Content $launcher
$mp=Join-Path $release 'manifest.json';$manifest=Get-Content $mp -Raw|ConvertFrom-Json
$manifest.name='Forest Playtest Batch 03';$manifest.version='0.10.5-batch03';$manifest.acceptance='Native client and server acceptance, saved-region migration/reload, and file-preservation checks. See Evidence/Batch03.'
$files=@{};foreach($f in $manifest.files){$files[$f.path]=$f.sha256}
foreach($f in @((Get-ChildItem (Join-Path $release 'Mods') -Recurse -File)) + @((Get-ChildItem (Join-Path $release 'Evidence/Batch03') -File))){$files[$f.FullName.Substring($release.Length+1).Replace('\','/')]=(Get-FileHash $f.FullName).Hash}
foreach($n in @('BATCH-03.txt','START-HERE.txt','Play-Allium.ps1')){$files[$n]=(Get-FileHash (Join-Path $release $n)).Hash}
$manifest.files=@($files.Keys|Sort-Object|ForEach-Object {@{path=$_;sha256=$files[$_]}});$manifest|ConvertTo-Json -Depth 8|Set-Content $mp
& (Join-Path $release 'Verify-Package.ps1')
Copy-Item (Join-Path $data 'Mods') (Join-Path $backup 'InstalledMods') -Recurse
Copy-Item (Join-Path $root 'artifacts/batch-03/migrated-save/Region/*') (Join-Path $save 'Region') -Force
Copy-Item (Join-Path $root 'artifacts/batch-03/migrated-save/blockmappings.nim') $save -Force
foreach($m in Get-ChildItem (Join-Path $release 'Mods') -Directory){Copy-Item $m.FullName (Join-Path $data 'Mods') -Recurse -Force}
foreach($f in $preserved){if((Get-FileHash $f.path).Hash -ne $f.hash){throw "Saved data changed unexpectedly: $($f.path)"}}
$release|Set-Content (Join-Path $root 'dist/latest-first-forest-release.txt')
Write-Output "Installed Batch 03; preserved $($preserved.Count) non-region save files. Release: $release"
