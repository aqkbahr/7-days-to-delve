$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$audit=Join-Path $root 'artifacts/validation/station-progression'
$base=(Get-Content (Join-Path $audit 'base.txt') -Raw).Trim()
& (Join-Path $base 'Verify-Package.ps1')
$release=Join-Path $root ('dist/Delve-Crafting-Stations-'+(Get-Date -Format yyyyMMdd-HHmmss))
$manifest=Get-Content (Join-Path $base 'manifest.json') -Raw|ConvertFrom-Json
New-Item -ItemType Directory $release|Out-Null
foreach($entry in $manifest.files){
 if($entry.path -eq 'manifest.json'){continue}
 $target=Join-Path $release $entry.path
 New-Item -ItemType Directory (Split-Path $target) -Force|Out-Null
 if($entry.path -match '^(Mods|Worlds)/' -and [IO.Path]::GetPathRoot($base) -eq [IO.Path]::GetPathRoot($release)){
  New-Item -ItemType HardLink -Path $target -Target (Join-Path $base $entry.path)|Out-Null
 }else{Copy-Item -LiteralPath (Join-Path $base $entry.path) -Destination $target}
}
$modName='ZZZZZZZZZZDelveCraftingStations'
$mod=Join-Path $release ('Mods/'+$modName)
New-Item -ItemType Directory $mod|Out-Null
foreach($name in @('ModInfo.xml','DelveCraftingStations.dll','Config')){Copy-Item (Join-Path $root ('src/'+$modName+'/'+$name)) $mod -Recurse}
Copy-Item (Join-Path $audit 'catalogue.json') (Join-Path $release 'Catalogue/first-playtest.json') -Force
Copy-Item (Join-Path $audit 'CRAFTING-STATIONS.txt') (Join-Path $release 'CRAFTING-STATIONS.txt')
Copy-Item (Join-Path $audit 'CRAFTING-STATIONS.txt') (Join-Path $release 'Catalogue/forest-ready-catalogue.txt') -Force
Copy-Item (Join-Path $root 'docs/station-progression-playtest.txt') (Join-Path $release 'START-HERE.txt') -Force
foreach($name in @('CRAFTING-GUIDE.txt','PROCESSING-GUIDE.txt','M3-PLAYTEST.txt','M3-EQUIPMENT-SPELLS.txt','FIRST-PLAYTHROUGH.txt')){
 $path=Join-Path $release $name
 if(Test-Path $path){("CRAFTING UPDATE: Use CRAFTING-STATIONS.txt for current recipe ranks and station requirements. Earlier crafting locations and progression notes below are historical; equipment stats and other playtest checks still apply.`n`n"+(Get-Content $path -Raw))|Set-Content $path}
}
$launcher=Join-Path $release 'Play-Allium.ps1'
(Get-Content $launcher -Raw).Replace('Proficiency recipe learning installed:','Crafting stations installed:')|Set-Content $launcher
$manifest.name='Allium Crafting Split and Station Progression';$manifest.version='0.11.0-candidate'
$manifest.files=@(Get-ChildItem $release -Recurse -File|Sort-Object FullName|ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest|ConvertTo-Json -Depth 6|Set-Content (Join-Path $release 'manifest.json')
& (Join-Path $release 'Verify-Package.ps1')
$release|Set-Content (Join-Path $audit 'candidate.txt')
Write-Host "Candidate: $release"

