# Update the selected playable package; preserve its existing world and player saves.
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if(Get-Process 7DaysToDie -ErrorAction SilentlyContinue){throw 'Close game and isolated tests before packaging.'}
$release=[IO.Path]::GetFullPath((Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim())
$dist=[IO.Path]::GetFullPath((Join-Path $root 'dist'))+[IO.Path]::DirectorySeparatorChar
if(!$release.StartsWith($dist,[StringComparison]::OrdinalIgnoreCase)){throw 'Package must be inside workspace dist.'}
& (Join-Path $release 'Verify-Package.ps1')
$evidence=Join-Path $root 'artifacts/validation/batch01'
foreach($name in @('batchone.txt','wagon-flow.txt','onboarding.txt','rank20.txt','recipes.txt','core.txt','integration.txt','recruit-definitions.txt','recruit-flow.txt','resurrection.txt','horde.txt','incursion.txt')){
 $text=Get-Content (Join-Path $evidence $name) -Raw
 if($text -notmatch 'PASS' -or $text -match '\] FAIL|^FAIL'){throw "Missing acceptance: $name"}
}
$tested=Get-Content (Join-Path $evidence 'tested-mods.json') -Raw|ConvertFrom-Json
foreach($f in $tested){
 $updated=$f.path -like 'Mods/ZZZDelveBatch01/*' -or $f.path -in @('Mods/Delve/Delve.dll','Mods/Delve/Config/buffs.xml','Mods/Delve/Config/recipes.xml')
 $source=if($updated){Join-Path $root ('src/'+$f.path.Substring(5))}else{Join-Path $release $f.path}
 if((Get-FileHash -LiteralPath $source).Hash -ne $f.sha256){throw "Candidate differs from tested build: $source"}
}
$overlay=[ordered]@{
 'Mods/Delve/Delve.dll'=(Join-Path $root 'src/Delve/Delve.dll')
 'Mods/Delve/Config/buffs.xml'=(Join-Path $root 'src/Delve/Config/buffs.xml')
 'Mods/Delve/Config/recipes.xml'=(Join-Path $root 'src/Delve/Config/recipes.xml')
 'Catalogue/first-playtest.json'=(Join-Path $root 'src/Forest/first-playtest.json')
 'FOREST-READY-CATALOGUE.txt'=(Join-Path $root 'docs/forest-ready-catalogue.txt')
 'BATCH-01.txt'=(Join-Path $root 'docs/playtest-batch-01.txt')
}
$module=Join-Path $root 'src/ZZZDelveBatch01'
foreach($file in Get-ChildItem $module -Recurse -File){$overlay['Mods/ZZZDelveBatch01/'+$file.FullName.Substring($module.Length+1).Replace('\','/')]=$file.FullName}
foreach($file in Get-ChildItem $evidence -File){$overlay['Evidence/Batch01/'+$file.Name]=$file.FullName}
$backup=Join-Path $root ('artifacts/batch-01/backup-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
$changed=@($overlay.Keys)+@('START-HERE.txt','Play-Allium.ps1','manifest.json')
foreach($relative in $changed){$existing=Join-Path $release $relative;if(Test-Path -LiteralPath $existing){$copy=Join-Path $backup $relative;New-Item -ItemType Directory -Path (Split-Path $copy) -Force|Out-Null;Copy-Item -LiteralPath $existing -Destination $copy}}
$saves=Join-Path $release 'PlaytestData/Saves'
if(Test-Path $saves){Copy-Item -LiteralPath $saves -Destination (Join-Path $backup 'Saves') -Recurse}
$saveHashes=@(Get-ChildItem $saves -Recurse -File|ForEach-Object {@{path=$_.FullName;hash=(Get-FileHash -LiteralPath $_.FullName).Hash}})
foreach($relative in $overlay.Keys){$destination=Join-Path $release $relative;New-Item -ItemType Directory -Path (Split-Path $destination) -Force|Out-Null;Copy-Item -LiteralPath $overlay[$relative] -Destination $destination -Force}
$start=Join-Path $release 'START-HERE.txt'
"BATCH 01 - 0.10.1`r`nContinue your existing Allium-v0.10 save. Do not start over for this update.`r`nUse Play-First-Forest.cmd. Read BATCH-01.txt for changes and focused checks.`r`n`r`nPRIOR RELEASE NOTES`r`n"+(Get-Content $start -Raw)|Set-Content $start -Encoding utf8
$launcher=Join-Path $release 'Play-Allium.ps1'
(Get-Content $launcher -Raw).Replace('Allium exploration alpha: select NEW GAME, world $worldName, and a new game name.','Batch 01 installed: select CONTINUE GAME and your existing Allium-v0.10 save.')|Set-Content $launcher -Encoding utf8
$manifestPath=Join-Path $release 'manifest.json';$manifest=Get-Content $manifestPath -Raw|ConvertFrom-Json
$manifest.name='Forest Playtest Batch 01';$manifest.version='0.10.1-batch01'
$manifest|Add-Member -NotePropertyName acceptance -NotePropertyValue 'Native recipe/unlock, wagon storage/stages, rendered assets and Forest regression suite passed. Human gameplay and distant visuals remain playtest observations.' -Force
$files=@{};foreach($entry in $manifest.files){$files[$entry.path]=$entry.sha256}
foreach($relative in ($changed|Where-Object {$_ -ne 'manifest.json'})){$files[$relative]=(Get-FileHash -LiteralPath (Join-Path $release $relative)).Hash}
$manifest.files=@($files.Keys|Sort-Object|ForEach-Object {@{path=$_;sha256=$files[$_]}})
$manifest|ConvertTo-Json -Depth 8|Set-Content $manifestPath -Encoding utf8
foreach($f in $saveHashes){if((Get-FileHash -LiteralPath $f.path).Hash -ne $f.hash){throw "Save changed during deployment: $($f.path)"}}
& (Join-Path $release 'Verify-Package.ps1')
$backup|Set-Content (Join-Path $root 'artifacts/batch-01/latest-backup.txt')
Write-Host "Batch 01 applied in place: $release"
Write-Host "Backed up package files and $($saveHashes.Count) unchanged save files: $backup"
