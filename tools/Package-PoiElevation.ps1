param([string]$OutputRoot='D:/DelveBuilds')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$base=(Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim()
& (Join-Path $base 'Verify-Package.ps1')
$profile=Join-Path $root 'playtest/PoiElevation'
foreach($name in @('placement-audit','native-survey','native-wayrest')){
 $result=Get-Content (Join-Path $root ('artifacts/validation/poi-elevation/'+$name+'.txt')) -Raw
 if($result -notmatch '^PASS' -or $result -match 'FAIL'){throw "Elevation acceptance missing: $name"}
}
$release=Join-Path $OutputRoot ('Delve-POI-Elevation-'+(Get-Date -Format yyyyMMdd-HHmmss))
New-Item -ItemType Directory $release|Out-Null
$manifest=Get-Content (Join-Path $base 'manifest.json') -Raw|ConvertFrom-Json
foreach($entry in $manifest.files){
 $target=Join-Path $release $entry.path
 New-Item -ItemType Directory (Split-Path $target) -Force|Out-Null
 Copy-Item -LiteralPath (Join-Path $base $entry.path) -Destination $target
 if($entry.path.StartsWith('Mods/')){
  if((Get-FileHash $target).Hash -ne (Get-FileHash (Join-Path $profile $entry.path)).Hash){throw "Latest gameplay module differs from test: $($entry.path)"}
 }
}
$world=Join-Path $release 'Worlds/Allium-v0.10'
& 'C:/Users/Michael/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' (Join-Path $PSScriptRoot 'fix_allium_poi_elevation.py') $world --metadata-root $release
if($LASTEXITCODE -ne 0){throw 'Elevation correction failed'}
foreach($file in Get-ChildItem $world -File){
 if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash (Join-Path $profile ('GeneratedWorlds/Allium-v0.10/'+$file.Name))).Hash){throw "World differs from tested input: $($file.Name)"}
}
foreach($name in @('locations.json','dungeons.json')){if(Test-Path (Join-Path $world $name)){Copy-Item (Join-Path $world $name) (Join-Path $release $name) -Force}}
(Join-Path $release 'PlaytestData')|Set-Content (Join-Path $release 'save-data-location.txt')
$launcher=Join-Path $release 'Play-Allium.ps1'
$text=Get-Content $launcher -Raw
$text=$text.Replace('Batch 04 installed: select CONTINUE GAME and your existing Allium-v0.10 save.','POI elevations corrected: select NEW GAME, Allium-v0.10, and a new save name.')
$text=$text.Replace('Skill coverage installed: select CONTINUE GAME and your existing Allium-v0.10 save.','POI elevations corrected: select NEW GAME, Allium-v0.10, and a new save name.')
$text|Set-Content $launcher
Copy-Item (Join-Path $root 'docs/poi-elevation-playtest.txt') (Join-Path $release 'START-HERE.txt')
Copy-Item (Join-Path $root 'docs/poi-elevation-playtest.txt') (Join-Path $release 'POI-ELEVATION.txt')
New-Item -ItemType Directory (Join-Path $release 'Evidence/PoiElevation') -Force|Out-Null
Copy-Item (Join-Path $root 'artifacts/validation/poi-elevation/*') (Join-Path $release 'Evidence/PoiElevation')
$sourcesPath=Join-Path $release 'sources.json'
$sources=if(Test-Path $sourcesPath){Get-Content $sourcesPath -Raw|ConvertFrom-Json}else{[pscustomobject]@{}}
$sources|Add-Member -NotePropertyName poiElevation -NotePropertyValue @{base=$base;nativeTest='Isolated PoiElevationApron';correction='500 POIs +1m, 12 church POIs +2m, level aprons with smooth outer blend; 377 ore sites unchanged';acceptance='Native 512-site perimeter layer survey and generated Wayrest columns; full visual traversal remains'} -Force
$sources|ConvertTo-Json -Depth 15|Set-Content $sourcesPath
$manifest.name='Allium Flush POI Elevations'
$manifest.version=$manifest.version+'-poi-elevation'
$manifest.files=@(Get-ChildItem $release -Recurse -File|Where-Object Name -ne 'manifest.json'|Sort-Object FullName|ForEach-Object{@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json')
& (Join-Path $release 'Verify-Package.ps1')
if((Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim() -ne $base){throw 'Active build changed during packaging; leave candidate unselected'}
$release|Set-Content (Join-Path $root 'dist/latest-poi-elevation-release.txt')
$release|Set-Content (Join-Path $root 'dist/latest-first-forest-release.txt')
Write-Host "Selected corrected package: $release"
