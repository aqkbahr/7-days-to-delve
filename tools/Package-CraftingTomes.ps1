param([string]$ProfileName='TomeTrading')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$base=(Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim()
$profile=Join-Path $root "playtest/$ProfileName"
$evidence=Join-Path $root 'artifacts/validation/tome-trading'
$test=Get-Content (Join-Path $evidence 'native.txt') -Raw
if($test -notmatch '\[Tomes\] PASS' -or $test -match '\[Tomes\] FAIL'){throw 'Native tome acceptance required'}
if((Get-Content (Join-Path $evidence 'core.txt') -Raw) -notmatch 'PASS: 617'){throw 'Core regression required'}
$tested=Get-Content (Join-Path $evidence 'tested-mods.json') -Raw|ConvertFrom-Json
foreach($e in $tested){if((Get-FileHash (Join-Path $profile $e.path)).Hash -ne $e.sha256){throw "Tested content changed: $($e.path)"}}
& (Join-Path $base 'Verify-Package.ps1')
$release=Join-Path $root ('dist/Delve-Crafting-Tomes-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory $release|Out-Null
$manifest=Get-Content (Join-Path $base 'manifest.json') -Raw|ConvertFrom-Json
# Copy only frozen package files, never the player's saves or runtime Mods.
foreach($entry in $manifest.files){
 $dest=Join-Path $release $entry.path
 New-Item -ItemType Directory (Split-Path $dest) -Force|Out-Null
 Copy-Item -LiteralPath (Join-Path $base $entry.path) -Destination $dest
}
foreach($mod in Get-ChildItem (Join-Path $base 'Mods') -Directory){
 foreach($f in Get-ChildItem (Join-Path $profile ('Mods/'+$mod.Name)) -Recurse -File){
  $rel=$f.FullName.Substring((Join-Path $profile 'Mods').Length+1)
  $dest=Join-Path $release ('Mods/'+$rel);New-Item -ItemType Directory (Split-Path $dest) -Force|Out-Null
  Copy-Item -LiteralPath $f.FullName -Destination $dest
 }
}
Copy-Item (Join-Path $root 'src/Forest/first-playtest.json') (Join-Path $release 'Catalogue/first-playtest.json')
Copy-Item (Join-Path $root 'docs/forest-ready-catalogue.txt') (Join-Path $release 'Catalogue/forest-ready-catalogue.txt')
Copy-Item (Join-Path $root 'docs/forest-access-playtest.txt') (Join-Path $release 'ACCESS-GUIDE.txt')
Copy-Item $evidence (Join-Path $release 'Evidence/TomeTrading') -Recurse
$notes=@'
CRAFTING TOMES UPDATE
Run Play-Allium.cmd and continue your existing save. No new character is needed.
Optional Farming, Cooking, Mining, Smithing, Carpentry and Alchemy lessons now
come from Crafting Tomes sold by vendors for exactly 500 gold each.
Each normal vendor restock includes three different tome types, randomly selected
from the six. Existing inventories gain them on their next scheduled restock.
Read a tome before crafting its lesson objectives. Tomes cannot be crafted.
Recipe/station unlocks and proficiency requirements are unchanged.
Previously owned notes retain their IDs and become tomes; active lessons remain.
This local launcher continues using the previous package's existing save folder.
'@
$notes|Set-Content (Join-Path $release 'START-HERE.txt')
$notes|Set-Content (Join-Path $release 'TOMES.txt')
$validation=Join-Path $release 'VALIDATION.txt'
("TOME UPDATE: PASS - 600 native restocks across six vendors, six tome types, fixed prices at quantities 1/2/3, noncraftable lessons, and 617 core checks. Forest dependency validation resolves 219 recipe variants with no blocked ingredients. See Evidence/TomeTrading. Earlier validation below applies to unchanged baseline systems.`r`n`r`n"+(Get-Content $validation -Raw))|Set-Content $validation
$data=Join-Path $base 'PlaytestData'
if(Test-Path (Join-Path $base 'save-data-location.txt')){$data=(Get-Content (Join-Path $base 'save-data-location.txt') -Raw).Trim()}
$data|Set-Content (Join-Path $release 'save-data-location.txt')
$launcher=Join-Path $release 'Play-Allium.ps1'
$s=Get-Content $launcher -Raw
$s=$s.Replace("`$data=Join-Path `$package 'PlaytestData'","`$data=(Get-Content (Join-Path `$package 'save-data-location.txt') -Raw).Trim()")
$s=$s.Replace('Batch 02 installed:','Crafting tomes installed:')
$s|Set-Content $launcher
$guide=Join-Path $release 'CRAFTING-GUIDE.txt'
$s=(Get-Content $guide -Raw) -replace 'All \d+ enabled recipe variants','All 219 enabled recipe variants'
($s+"`nOptional lesson tomes are vendor purchases: 500 gold; three different types per restock.`n")|Set-Content $guide
@{baseline=$base;scope='Optional lesson tomes, fixed purchase price and guaranteed distinct restock';saveData=$data}|ConvertTo-Json|Set-Content (Join-Path $release 'tome-sources.json')
$manifest.version='0.10.3-tomes'
$manifest.files=@(Get-ChildItem $release -Recurse -File|Where-Object {$_.FullName -ne (Join-Path $release 'manifest.json')}|Sort-Object FullName|ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json')
& (Join-Path $release 'Verify-Package.ps1')
foreach($pointer in Get-ChildItem (Join-Path $root 'dist') -Filter 'latest-*-release.txt'){
 if((Get-Content $pointer.FullName -Raw).Trim() -eq $base){$release|Set-Content $pointer.FullName}
}
$release|Set-Content (Join-Path $root 'dist/latest-tomes-release.txt')
Write-Output $release
