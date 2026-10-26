$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$source=(Get-Content (Join-Path $root 'artifacts/forest-base-release.txt') -Raw).Trim()
& (Join-Path $source 'Verify-Package.ps1')
$report=Get-Content (Join-Path $root 'artifacts/validation/forest/content.json') -Raw|ConvertFrom-Json
if($report.result -ne 'PASS'){throw 'Forest static checks did not pass'}
$runtime=Get-Content (Join-Path $root 'artifacts/validation/forest/definitions.txt') -Raw
if($runtime -notmatch '\[Forest\] PASS: 10 native entities'){throw 'No passing live bestiary validation'}
$release=Join-Path $root ('dist/Delve-ForestBestiary-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $release -Force|Out-Null
# The pinned released core avoids shipping unrelated in-progress advancement.
foreach($name in @('Mods','Worlds')) {Copy-Item (Join-Path $source $name) $release -Recurse}
Copy-Item (Join-Path $root 'src/ZDelveForest') (Join-Path $release 'Mods') -Recurse
foreach($file in Get-ChildItem (Join-Path $root 'src/ZDelveForest') -Recurse -File) {
 $relative=$file.FullName.Substring((Join-Path $root 'src/ZDelveForest').Length+1)
 if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash (Join-Path $root "playtest/ForestBestiary/Mods/ZDelveForest/$relative")).Hash){throw "Untested module file: $relative"}
}
Copy-Item (Join-Path $source 'world-name.txt') $release
foreach($name in @('Play-Allium.cmd','Play-Allium.ps1','Verify-Package.ps1')) {Copy-Item (Join-Path $source $name) $release}
foreach($name in @('locations.json','locations-atlas.png')) {if(Test-Path (Join-Path $source $name)){Copy-Item (Join-Path $source $name) $release}}
Copy-Item (Join-Path $root 'docs/forest-bestiary-playtest.txt') (Join-Path $release 'START-HERE.txt')
Copy-Item (Join-Path $root 'docs/forest-bestiary-validation.txt') (Join-Path $release 'VALIDATION.txt')
Copy-Item (Join-Path $root 'src/ZDelveForest/Bestiary.xml') $release
$manifest=@{name='7 Days to Delve - Forest Bestiary';version='forest-bestiary-1';gameVersion='3.3.0 (b18)';baseRelease=(Split-Path $source -Leaf);files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File|Sort-Object FullName|ForEach-Object{@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release|Set-Content (Join-Path $root 'dist/latest-forest-bestiary-release.txt') -Encoding utf8
Write-Host "Forest bestiary package: $release"
