$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$base=(Get-Content (Join-Path $root 'artifacts/recipe-learning-base.txt') -Raw).Trim()
$release=(Get-Content (Join-Path $root 'artifacts/recipe-learning-package.txt') -Raw).Trim()
$profile=Join-Path $root 'playtest/RecipeLearning'
$evidence=Join-Path $root 'artifacts/validation/recipe-learning'
foreach($pair in @(@('core','PASS: 617'),@('recipes','\[ForestReady\] PASS 219'),@('merged-runtime','PASS: engine-merged'))){
 $text=Get-Content (Join-Path $evidence ($pair[0]+'.txt')) -Raw
 if($text -notmatch $pair[1] -or $text -match '\] FAIL|Exception'){throw "Missing passing evidence: $($pair[0])"}
}
$audit=Get-Content (Join-Path $evidence 'audit.json') -Raw|ConvertFrom-Json
if($audit.result -ne 'PASS' -or $audit.base -ne $base){throw 'Audit base mismatch'}
$tested=@(Get-ChildItem (Join-Path $release 'Mods') -Recurse -File|ForEach-Object {
 $relative=$_.FullName.Substring($release.Length+1)
 $hash=(Get-FileHash $_.FullName).Hash
 if((Get-FileHash (Join-Path $profile $relative)).Hash -ne $hash){throw "Tested file differs: $relative"}
 @{path=$relative.Replace('\','/');sha256=$hash}
})
$tested|ConvertTo-Json -Depth 4|Set-Content (Join-Path $evidence 'tested-mods.json')
Copy-Item $evidence (Join-Path $release 'Evidence/RecipeLearning') -Recurse
$validation=Join-Path $release 'VALIDATION.txt'
("RECIPE LEARNING UPDATE: 617 core checks, all 219 native recipe boundaries/ingredients, and engine-merged magazine removal pass. Static audit covers 759 variants and preserves 73 schematic definitions, perk books and lesson tomes. Later content remains deferred; human UI and multiplayer are not validated. See Evidence/RecipeLearning. Historical baseline evidence follows.`n`n"+(Get-Content $validation -Raw))|Set-Content $validation
$manifest=Get-Content (Join-Path $release 'manifest.json') -Raw|ConvertFrom-Json
$manifest.version='0.10.6-recipe-learning'
$manifest.files=@(Get-ChildItem $release -Recurse -File|Where-Object {$_.FullName -ne (Join-Path $release 'manifest.json')}|Sort-Object FullName|ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json')
& (Join-Path $release 'Verify-Package.ps1')
$current=(Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim()
if($current -ne $base){throw 'A newer build was selected concurrently; preserve it and reconcile before selecting this package.'}
$base|Set-Content (Join-Path $root 'dist/previous-first-forest-release.txt')
$release|Set-Content (Join-Path $root 'dist/latest-first-forest-release.txt')
$release|Set-Content (Join-Path $root 'dist/latest-recipe-learning-release.txt')
Write-Host "Selected full Allium update: $release"
