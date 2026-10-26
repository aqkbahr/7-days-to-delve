$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$base=(Get-Content (Join-Path $root 'artifacts/recipe-learning-base.txt') -Raw).Trim()
& (Join-Path $base 'Verify-Package.ps1')
$release=Join-Path $root ('dist/Delve-Recipe-Learning-'+(Get-Date -Format yyyyMMdd-HHmmss))
New-Item -ItemType Directory $release|Out-Null
$manifest=Get-Content (Join-Path $base 'manifest.json') -Raw|ConvertFrom-Json
# Only immutable package files; never copy the user's saves/logs/runtime folder.
foreach($entry in $manifest.files){
 $target=Join-Path $release $entry.path
 New-Item -ItemType Directory (Split-Path $target) -Force|Out-Null
 Copy-Item -LiteralPath (Join-Path $base $entry.path) -Destination $target
}
Copy-Item (Join-Path $root 'src/ZZZZZZZZDelveRecipeLearning') (Join-Path $release 'Mods') -Recurse
Copy-Item (Join-Path $root 'docs/recipe-learning-playtest.txt') (Join-Path $release 'START-HERE.txt')
Copy-Item (Join-Path $root 'docs/recipe-learning-playtest.txt') (Join-Path $release 'RECIPE-LEARNING.txt')
$launcher=Join-Path $release 'Play-Allium.ps1'
(Get-Content $launcher -Raw).Replace('Batch 03 installed:','Proficiency recipe learning installed:')|Set-Content $launcher
$manifest.name='Allium Proficiency Recipe Learning'
$manifest.version='0.10.6-recipe-learning'
$manifest.files=@(Get-ChildItem $release -Recurse -File|Sort-Object FullName|ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json')
& (Join-Path $release 'Verify-Package.ps1')
$release|Set-Content (Join-Path $root 'artifacts/recipe-learning-package.txt')
Write-Host "Candidate awaiting engine checks: $release"
