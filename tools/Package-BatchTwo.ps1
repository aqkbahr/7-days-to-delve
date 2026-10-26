$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$release=[IO.Path]::GetFullPath((Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim())
if(!$release.StartsWith([IO.Path]::GetFullPath((Join-Path $root 'dist'))+[IO.Path]::DirectorySeparatorChar)){throw 'Release outside workspace dist'}
if(Get-Process 7DaysToDie -ErrorAction SilentlyContinue){throw 'Close isolated tests before packaging'}
& (Join-Path $release 'Verify-Package.ps1')
$candidate=Join-Path $root 'artifacts/batch-02/candidate'
$evidence=Join-Path $root 'artifacts/validation/batch02'
foreach($name in @('onboarding','rank20','recipes','core','integration','recruit-definitions','recruit-flow','resurrection','horde','incursion')){
 $result=Get-Content (Join-Path $evidence ($name+'.txt')) -Raw
 if($result -notmatch 'PASS' -or $result -match '\] FAIL|^FAIL'){throw "Missing acceptance $name"}
}
foreach($name in @('ui','interactions')){if((Get-Content (Join-Path $evidence ($name+'.txt')) -Raw) -notmatch "PASS .*fixture completed"){throw "Missing client acceptance $name"}}
$migration=Join-Path $root 'playtest/BatchTwoSave/Mods/BatchTwoSaveTools'
if((Get-Content (Join-Path $migration 'migration-audit.txt') -Raw) -notmatch 'TERRAIN eligible=0.*already=3896'){throw 'Missing migration reload audit'}
$tested=Get-Content (Join-Path $evidence 'tested-mods-reload.json') -Raw|ConvertFrom-Json
foreach($f in $tested){if((Get-FileHash -LiteralPath (Join-Path $candidate $f.path)).Hash -ne $f.sha256){throw "Candidate differs from tested build $($f.path)"}}
$preflight=(Get-Content (Join-Path $root 'artifacts/batch-02/preflight-backup.txt') -Raw).Trim()
$save=Join-Path $release 'PlaytestData/Saves/Allium-v0.10/ForestTest01'
$original=Join-Path $preflight 'Saves/Allium-v0.10/ForestTest01'
$repaired=Join-Path $root 'playtest/BatchTwoSave/Saves/Allium-v0.10/ForestTest01'
foreach($f in Get-ChildItem $original -Recurse -File){$relative=$f.FullName.Substring($original.Length+1);if((Get-FileHash $f.FullName).Hash -ne (Get-FileHash (Join-Path $save $relative)).Hash){throw "Playable save changed after preflight: $relative"}}
$backup=Join-Path $root ('artifacts/batch-02/package-backup-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $backup -Force|Out-Null
Copy-Item (Join-Path $release 'Mods') $backup -Recurse
foreach($n in @('manifest.json','START-HERE.txt','Play-Allium.ps1')){Copy-Item (Join-Path $release $n) $backup}
Copy-Item (Join-Path $release 'Worlds/Allium-v0.10/dtm.raw') (Join-Path $backup 'dtm.raw')
# The copied migration changes regions and appends block mappings only. Character,
# world time, quests, roster, treasury, and all other saved data remain original.
$preserved=@(Get-ChildItem $save -Recurse -File|Where-Object {$_.FullName -notlike "$save\Region\*" -and $_.Name -ne 'blockmappings.nim'}|ForEach-Object {@{path=$_.FullName;hash=(Get-FileHash $_.FullName).Hash}})
foreach($mod in Get-ChildItem (Join-Path $candidate 'Mods') -Directory){Copy-Item $mod.FullName (Join-Path $release 'Mods') -Recurse -Force}
Copy-Item (Join-Path $repaired 'Region/*') (Join-Path $save 'Region') -Force
Copy-Item (Join-Path $repaired 'blockmappings.nim') $save -Force
$dtm=Join-Path $root 'artifacts/batch-02/apron-candidate/dtm.raw'
Copy-Item $dtm (Join-Path $release 'Worlds/Allium-v0.10/dtm.raw') -Force
Copy-Item $dtm (Join-Path $release 'PlaytestData/GeneratedWorlds/Allium-v0.10/dtm.raw') -Force
Copy-Item (Join-Path $root 'docs/playtest-batch-02.txt') (Join-Path $release 'BATCH-02.txt') -Force
New-Item -ItemType Directory (Join-Path $release 'Evidence/Batch02') -Force|Out-Null
Copy-Item (Join-Path $evidence '*') (Join-Path $release 'Evidence/Batch02') -Force
Copy-Item (Join-Path $root 'src/Forest/first-playtest.json') (Join-Path $release 'Catalogue/first-playtest.json') -Force
"BATCH 02 - 0.10.2`r`nContinue ForestTest01 in Allium-v0.10. Your character and progress are preserved.`r`nRead BATCH-02.txt for changes and focused rechecks.`r`n"|Set-Content (Join-Path $release 'START-HERE.txt')
$launcher=Join-Path $release 'Play-Allium.ps1';(Get-Content $launcher -Raw).Replace('Batch 01 installed:','Batch 02 installed:')|Set-Content $launcher
foreach($f in $preserved){if((Get-FileHash $f.path).Hash -ne $f.hash){throw "Unexpected saved-data change $($f.path)"}}
$mp=Join-Path $release 'manifest.json';$manifest=Get-Content $mp -Raw|ConvertFrom-Json
$manifest.name='Forest Playtest Batch 02';$manifest.version='0.10.2-batch02';$manifest.acceptance='Native Forest suite, client dialogue/loot/harvest, authored container parity, and isolated saved-region migration/reload passed. Human balance and visual feedback remain playtest work.'
$files=@{};foreach($f in $manifest.files){$files[$f.path]=$f.sha256}
$changed=@(Get-ChildItem (Join-Path $release 'Mods') -Recurse -File)+@(Get-ChildItem (Join-Path $release 'Evidence/Batch02') -File)
foreach($f in $changed){$files[$f.FullName.Substring($release.Length+1).Replace('\','/')]=(Get-FileHash $f.FullName).Hash}
foreach($n in @('Worlds/Allium-v0.10/dtm.raw','BATCH-02.txt','START-HERE.txt','Play-Allium.ps1','Catalogue/first-playtest.json')){$files[$n]=(Get-FileHash (Join-Path $release $n)).Hash}
$manifest.files=@($files.Keys|Sort-Object|ForEach-Object {@{path=$_;sha256=$files[$_]}})
$manifest|ConvertTo-Json -Depth 8|Set-Content $mp
& (Join-Path $release 'Verify-Package.ps1')
$backup|Set-Content (Join-Path $root 'artifacts/batch-02/latest-package-backup.txt')
Write-Output "Batch 02 packaged. Preserved $($preserved.Count) non-region save files. Backup: $backup"
